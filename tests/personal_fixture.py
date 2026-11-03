"""Synthetic-only server for personal UI/pipeline validation; never loads real config."""
import io
import ipaddress
import json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import threading
import urllib.request
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server import PortalServer
from personal import identifier
from test_personal import FakeCloud
from media import process_options

class Fixture:
    def __init__(self,tracks=False,navigation=False,duration=20,live=False):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        subprocess.run([shutil.which('ffmpeg'),'-v','quiet','-f','lavfi','-i','testsrc2=size=320x180:rate=24','-f','lavfi','-i','sine=frequency=440','-t',str(duration),'-c:v','libx264','-pix_fmt','yuv420p','-g','48','-c:a','aac','-movflags','+faststart',str(self.root/'video.mp4')],check=True,**process_options())
        video=self.root/'video.mp4'
        if tracks:
            for language,line in (('pt','Legenda portuguesa'),('en','English caption')):
                (self.root/(language+'.srt')).write_text('1\n00:00:02,000 --> 00:00:08,000\n'+line+'\n\n2\n00:00:12,000 --> 00:00:18,000\n'+line+' final\n\n',encoding='utf-8')
            multi=self.root/'multilingual.mp4'
            subprocess.run([shutil.which('ffmpeg'),'-v','quiet','-i',str(video),'-f','lavfi','-i','sine=frequency=880','-i',str(self.root/'pt.srt'),'-i',str(self.root/'en.srt'),'-map','0:v:0','-map','0:a:0','-map','1:a:0','-map','2:s:0','-map','3:s:0','-t',str(duration),'-c:v','copy','-c:a','aac','-c:s','mov_text','-metadata:s:a:0','language=por','-metadata:s:a:1','language=eng','-metadata:s:s:0','language=por','-metadata:s:s:1','language=eng','-movflags','+faststart',str(multi)],check=True,timeout=20,**process_options())
            video=multi
        raw=video.read_bytes()
        class Source(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_HEAD(self):self.do_GET()
            def do_GET(self):
                match=re.fullmatch(r'bytes=(\d+)-(\d*)',self.headers.get('Range',''))
                start=int(match[1]) if match else 0;end=min(int(match[2]) if match and match[2] else len(raw)-1,len(raw)-1)
                if start>=len(raw):self.send_error(416);return
                self.send_response(206 if match else 200);self.send_header('Content-Type','video/mp4');self.send_header('Content-Length',str(end-start+1));self.send_header('Accept-Ranges','bytes')
                if match:self.send_header('Content-Range',f'bytes {start}-{end}/{len(raw)}')
                self.end_headers()
                if self.command!='HEAD':
                    try:self.wfile.write(raw[start:end+1])
                    except OSError:pass
        self.source=ThreadingHTTPServer(('127.0.0.1',0),Source);threading.Thread(target=self.source.serve_forever,daemon=True).start()
        cfg=dict(host='127.0.0.1',port=0,network=ipaddress.ip_network('127.0.0.0/24'),runtime_path=str(self.root/'runtime'),switch_delay_ms=1000,player_solution='ffmpeg')
        self.app=PortalServer(cfg,[],{},'test-control');self.app.config['loopback_port']=self.app.server_port;self.app.personal_media.app.config['loopback_port']=self.app.server_port
        source=self.source
        class Cloud(FakeCloud):
            def __init__(self):
                super().__init__();self.binary=urllib.request.build_opener(urllib.request.ProxyHandler({}))
                template=self.rows[0];self.rows=[dict(template,id='photo'+str(i),name='Fotografia '+str(i)+'.jpg') for i in range(15)]+[self.rows[1]]
            def content_url(self,drive,item):return 'http://127.0.0.1:'+str(source.server_port)+'/video.mp4'
            def folders(self,parent='root'):return dict(drive='drive',items=[dict(id='root',name='Pasta piloto sintética')])
            def state(self):return dict(connected=True,configured=True,error='',auth=None)
        self.app.personal.cloud.close();self.app.personal.cloud=Cloud();self.app.personal.add_root('root');roots=[dict(r) for r in self.app.personal.db.execute('SELECT * FROM roots')];self.app.personal._scan(roots)
        self.video=identifier('drive','video');self.photo=identifier('drive','photo0')
        self.app.catalog.add(dict(id='fixture-vod',kind='movie',name='Synthetic IPTV',group='Fixture',url='http://127.0.0.1:'+str(source.server_port)+'/video.mp4'))
        if live:self.app.catalog.add(dict(id='fixture-tv',kind='tv',name='Synthetic PT TV HD',country='PT',quality='HD',group='PT | Fixture',url='http://127.0.0.1:'+str(source.server_port)+'/video.mp4'))
        if navigation:
            url='http://127.0.0.1:'+str(source.server_port)+'/video.mp4'
            for i in range(60):self.app.catalog.add(dict(id='nav-'+str(i),kind='movie',name='List movie %03d'%i,group='Fixture',url=url))
        self.thread=threading.Thread(target=self.app.serve_forever,daemon=True);self.thread.start()
        self.url='http://127.0.0.1:'+str(self.app.server_port)
    def close(self):
        self.app.shutdown();self.app.server_close();self.source.shutdown();self.source.server_close();self.temp.cleanup()

if __name__=='__main__':
    f=Fixture(tracks="--tracks" in sys.argv,navigation="--navigation" in sys.argv,duration=120 if "--long" in sys.argv else 20,live="--live" in sys.argv)
    Path(sys.argv[1]).write_text(json.dumps(dict(url=f.url,video=f.video,photo=f.photo)))
    stop=Path(sys.argv[1]+'.stop');stop.unlink(missing_ok=True)
    print('Synthetic personal server ready',flush=True)
    try:
        while not stop.exists():time.sleep(.25)
    except KeyboardInterrupt:pass
    finally:f.close()
