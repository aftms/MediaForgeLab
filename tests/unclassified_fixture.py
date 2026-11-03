import ipaddress,json,sys,tempfile,threading,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server import PortalServer
temp=tempfile.TemporaryDirectory();app=PortalServer(dict(host='127.0.0.1',port=0,network=ipaddress.ip_network('127.0.0.0/24'),runtime_path=temp.name,switch_delay_ms=1000,player_solution='ffmpeg'),[],{},'test')
c=app.collections;category=c.update(dict(operation='category-save',name='Culinária'))['id'];a=c.update(dict(operation='item-save',url='https://www.youtube.com/watch?v=M7lc1UVf-VE',title='Vídeo por classificar'))['id'];b=c.update(dict(operation='item-save',url='https://vimeo.com/76979871',title='Receita classificada',categories=[category]))['id']
threading.Thread(target=app.serve_forever,daemon=True).start();out=Path(sys.argv[1]);out.write_text(json.dumps(dict(url='http://127.0.0.1:'+str(app.server_port),category=category,unclassified=a,classified=b)));stop=Path(str(out)+'.stop');stop.unlink(missing_ok=True);print('Unclassified fixture ready',flush=True)
try:
 while not stop.exists():time.sleep(.3)
finally:app.shutdown();app.server_close();temp.cleanup()
