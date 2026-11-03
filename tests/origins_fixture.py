import ipaddress,json,sys,tempfile,threading,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server import PortalServer
temp=tempfile.TemporaryDirectory();items=[]
for id,name in enumerate(('MEO: RTP 1 HD','VO: RTP 1 FHD','MEO: SPORT TV 1 HD','VO: SPORT TV 2 HD','NOS: SPORT TV 3 HD','PT: RTP 2 HD'),1):items.append(dict(id=str(id),kind='tv',name=name,group='PT| Portugal',url='https://fixture.invalid/'+str(id)))
app=PortalServer(dict(host='127.0.0.1',port=0,network=ipaddress.ip_network('127.0.0.0/24'),runtime_path=temp.name,switch_delay_ms=1000,player_solution='ffmpeg'),items,{},'test')
threading.Thread(target=app.serve_forever,daemon=True).start();out=Path(sys.argv[1]);out.write_text(json.dumps(dict(url='http://127.0.0.1:'+str(app.server_port))))
stop=Path(str(out)+'.stop');stop.unlink(missing_ok=True);print('Origins fixture ready',flush=True)
try:
 while not stop.exists():time.sleep(.3)
finally:app.shutdown();app.server_close();temp.cleanup()
