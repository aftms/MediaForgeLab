"""Real FFmpeg/HTTP integration against synthetic local media only."""
import ipaddress
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import PortalServer
from media import MediaError, process_options


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg required')
class PipelineTests(unittest.TestCase):
    def test_real_remux_transcode_seek_cleanup_and_supplier_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            ffmpeg=shutil.which('ffmpeg')
            for codec in ('libx264', 'mpeg4'):
                subprocess.run([ffmpeg,'-v','quiet','-f','lavfi','-i','testsrc2=size=160x90:rate=24',
                    '-f','lavfi','-i','sine=frequency=440','-t','6','-c:v',codec,'-pix_fmt','yuv420p',
                    '-g','24','-c:a','aac','-movflags','+faststart',str(root/(codec+'.mp4'))],
                    check=True,timeout=20,stdout=subprocess.DEVNULL,**process_options())

            class Source(BaseHTTPRequestHandler):
                def log_message(self, *args): pass
                def do_GET(self):
                    name=self.path.lstrip('/')
                    if name not in ('libx264.mp4','mpeg4.mp4'):
                        self.send_error(404);return
                    raw=(root/name).read_bytes()
                    match=re.fullmatch(r'bytes=(\d+)-(\d*)',self.headers.get('Range',''))
                    start=int(match[1]) if match else 0
                    end=min(int(match[2]),len(raw)-1) if match and match[2] else len(raw)-1
                    data=raw[start:end+1]
                    self.send_response(206 if match else 200)
                    self.send_header('Content-Type','video/mp4')
                    self.send_header('Content-Length',str(len(data)))
                    self.send_header('Accept-Ranges','bytes')
                    if match:self.send_header('Content-Range',f'bytes {start}-{end}/{len(raw)}')
                    self.end_headers()
                    try:self.wfile.write(data)
                    except OSError:pass

            source=ThreadingHTTPServer(('127.0.0.1',0),Source)
            source_thread=threading.Thread(target=source.serve_forever,daemon=True)
            source_thread.start()
            config=dict(host='127.0.0.1',port=0,network=ipaddress.ip_network('127.0.0.0/24'),
                runtime_path=str(root/'runtime'),switch_delay_ms=1000,player_solution='ffmpeg')
            app=PortalServer(config,[],{},'fixture-control')
            app.config['loopback_port']=app.server_port
            thread=threading.Thread(target=app.serve_forever,daemon=True)
            thread.start()
            try:
                for codec,expected in (('libx264','remux'),('mpeg4','transcode'),('native-tv','remux'),('missing','failure')):
                    identifier='m'+str(len(app.catalog.items)+1)
                    fast=codec=='native-tv'
                    app.catalog.add(dict(id=identifier,kind='tv' if fast else 'movie',name='Synthetic',group='Fixture',
                        url=f'http://127.0.0.1:{source.server_port}/{"libx264" if fast else codec}.mp4'))
                    if fast:app.media.ffprobe='must-not-run-for-native-tv'
                    else:app.media.ffprobe=shutil.which('ffprobe')
                    session=app.media.start(dict(id=identifier,owner='fixture-browser-owner',position=2,device='androidtv' if fast else 'web'),'127.0.0.1','web')
                    deadline=time.monotonic()+35
                    while time.monotonic()<deadline:
                        if not app.media.status()['active'] or app.media.status()['state']=='ready':break
                        time.sleep(.1)
                    if expected=='failure':
                        self.assertFalse(app.media.status()['active'])
                        with self.assertRaises(MediaError) as error:
                            app.media.pulse(session,'127.0.0.1')
                        self.assertEqual(error.exception.status,503)
                        self.assertNotIn('127.0.0.1',str(error.exception))
                        continue
                    ready=app.media.pulse(session,'127.0.0.1')
                    self.assertEqual(ready['state'],'ready')
                    self.assertEqual(ready['video_mode'],expected)
                    self.assertEqual(ready['position'],0 if fast else 2)
                    if not fast:self.assertGreater(ready['duration'],5)
                    playlist,_=app.media.segment(session['token'],'index.m3u8','127.0.0.1')
                    self.assertIn(b'#EXTM3U',playlist)
                    segment=next((root/'runtime'/'media'/session['token']).glob('s*.ts'))
                    probe=subprocess.run([shutil.which('ffprobe'),'-v','quiet','-show_streams','-of','json',str(segment)],
                        stdout=subprocess.PIPE,check=True,timeout=10,**process_options())
                    streams=json.loads(probe.stdout)['streams']
                    self.assertEqual(next(s for s in streams if s['codec_type']=='video')['codec_name'],'h264')
                    with self.assertRaises(MediaError):
                        app.media.start(dict(id=identifier,owner='second-browser-owner'),'127.0.0.1','web')
                    app.media.release(session,'127.0.0.1')
                    self.assertFalse(segment.parent.exists())
                    self.assertFalse(app.media.status()['active'])
            finally:
                app.shutdown();app.server_close();thread.join(2)
                source.shutdown();source.server_close();source_thread.join(2)


if __name__=='__main__':unittest.main()
