"""Loopback-only control panel. Uses the portal's verified instance/control API."""
import json
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import control

PORT=8092
ACTION=secrets.token_hex(24)
LOCK=threading.Lock()
PAGE='''<!doctype html><html lang="pt"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Media Forge Lab · Gestão</title><style>body{font:16px/1.6 system-ui;background:#101d29;color:#eaf2f5;max-width:850px;margin:50px auto;padding:24px}h1{color:#88d9c9}section{background:#192e3b;padding:24px;border:1px solid #38505e;border-radius:14px;margin:20px 0}button,a{display:inline-block;color:#fff0d9;background:#294a53;padding:10px 16px;border:1px solid #52727a;border-radius:8px;margin:5px;text-decoration:none;font:inherit;cursor:pointer}button:disabled{opacity:.4}p{color:#b6cbd3}#status{color:#e5c28b}small{color:#b6cbd3}</style><h1><img src="/brand.png" alt="" width="52" height="52" style="vertical-align:middle;margin-right:12px">Media Forge Lab</h1><p>Gestão do portal e da aplicação web · computador de casa</p><section><h2 id="status">A verificar…</h2><button data-action="start">Iniciar</button><button data-action="restart">Reiniciar</button><button data-action="stop">Parar</button><p id="message" role="status"></p></section><section><h2>Abrir</h2><a href="http://127.0.0.1:8091/web/" target="_blank" rel="noopener">Aplicação web · Windows</a><a href="https://192.168.1.240:8443/web/" target="_blank" rel="noopener">Aplicação web · HTTPS / Android</a><a href="http://192.168.1.240:8090/" target="_blank" rel="noopener">Interface MAG</a><p>A aplicação web permite reproduzir, pesquisar, gerir favoritos e atualizar o catálogo. A interface MAG usa o comando da box.</p></section><small>Não reinicie nem pare durante uma atualização do catálogo. Parar o serviço encerra as reproduções.</small><script src="/app.js"></script></html>'''
JS='''let token="";async function status(){try{let r=await fetch('/status',{cache:'no-store'});let s=await r.json();token=s.token;document.getElementById('status').textContent=s.running?'● Portal em funcionamento':'○ Portal parado';}catch{document.getElementById('status').textContent='Gestão indisponível';}}document.querySelectorAll('button').forEach(b=>b.onclick=async()=>{document.querySelectorAll('button').forEach(x=>x.disabled=true);document.getElementById('message').textContent='A executar…';try{let r=await fetch('/action',{method:'POST',headers:{'Content-Type':'application/json','X-MAG-Control-Action':token},body:JSON.stringify({action:b.dataset.action})});let s=await r.json();document.getElementById('message').textContent=s.message;await status();}catch{document.getElementById('message').textContent='Não foi possível concluir.';}finally{document.querySelectorAll('button').forEach(x=>x.disabled=false);}});status();setInterval(status,10000);'''


class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass

    def allowed(self):
        host='127.0.0.1:'+str(PORT)
        return (self.client_address[0]=='127.0.0.1' and self.headers.get_all('Host',[])==[host]
                and self.headers.get('Origin','http://'+host)=='http://'+host
                and self.headers.get('Sec-Fetch-Site')!='cross-site')

    def send(self,status,body,mime='application/json'):
        raw=body if isinstance(body,bytes) else body.encode() if isinstance(body,str) else json.dumps(body).encode()
        self.send_response(status)
        self.send_header('Content-Type',mime+'; charset=utf-8');self.send_header('Content-Length',str(len(raw)))
        self.send_header('Cache-Control','no-store');self.send_header('X-Frame-Options','DENY')
        self.send_header('Content-Security-Policy',"default-src 'self'; style-src 'unsafe-inline'; frame-ancestors 'none'")
        self.end_headers()
        if self.command!='HEAD':self.wfile.write(raw)

    def do_HEAD(self):self.do_GET()

    def do_GET(self):
        if not self.allowed():self.send(403,{});return
        if self.path=='/':self.send(200,PAGE,'text/html')
        elif self.path=='/brand.png':self.send(200,(Path(__file__).parent/'public/assets/media-forge-lab.png').read_bytes(),'image/png')
        elif self.path=='/app.js':self.send(200,JS,'application/javascript')
        elif self.path=='/health':self.send(200,{'app':'magforgelab-manager','status':'ok'})
        elif self.path=='/status':self.send(200,{'running':bool(control.live()),'token':ACTION})
        else:self.send(404,{})

    def do_POST(self):
        if not self.allowed() or self.path!='/action' or not secrets.compare_digest(self.headers.get('X-MAG-Control-Action',''),ACTION):
            self.send(403,{'message':'Pedido recusado.'});return
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<256:raise ValueError()
            action=json.loads(self.rfile.read(size)).get('action')
            if action not in ('start','stop','restart'):raise ValueError()
            if not LOCK.acquire(blocking=False):self.send(409,{'message':'Já existe uma operação em curso.'});return
            try:
                active=control.live()
                if active and action!='start' and control.request(active['url']+'/api/refresh').get('running'):
                    self.send(409,{'message':'Aguarde a atualização do catálogo terminar.'});return
                ok=True
                if action in ('stop','restart'):ok=control.stop()==0
                if ok and action in ('start','restart'):ok=control.start()==0
                self.send(200 if ok else 503,{'message':'Operação concluída.' if ok else 'Não foi possível iniciar. Consulte o estado local.'})
            finally:LOCK.release()
        except (OSError,ValueError):self.send(400,{'message':'Operação inválida ou indisponível.'})


if __name__=='__main__':
    server=ThreadingHTTPServer(('127.0.0.1',PORT),Handler)
    server.handle_error=lambda *args:None
    server.serve_forever()
