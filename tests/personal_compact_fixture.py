import ipaddress,json,sys,tempfile,threading,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));sys.path.insert(0,str(Path(__file__).resolve().parent))
from server import PortalServer
from test_personal import FakeCloud
temp=tempfile.TemporaryDirectory();app=PortalServer(dict(host='127.0.0.1',port=0,network=ipaddress.ip_network('127.0.0.0/24'),runtime_path=temp.name,switch_delay_ms=1000,player_solution='ffmpeg'),[],{},'test')
cloud=FakeCloud();template=cloud.rows[0];cloud.rows=[dict(template,id='photo'+str(i),name='Fotografia de teste com nome longo %03d.jpg'%i) for i in range(135)];app.personal.cloud.close();app.personal.cloud=cloud;app.personal.add_root('root');app.personal._scan([dict(r) for r in app.personal.db.execute('SELECT * FROM roots')]);threading.Thread(target=app.serve_forever,daemon=True).start()
out=Path(sys.argv[1]);out.write_text(json.dumps(dict(url='http://127.0.0.1:'+str(app.server_port))));stop=Path(str(out)+'.stop');stop.unlink(missing_ok=True);print('Compact metadata-only fixture ready',flush=True)
try:
 while not stop.exists():time.sleep(.3)
finally:app.shutdown();app.server_close();temp.cleanup()
