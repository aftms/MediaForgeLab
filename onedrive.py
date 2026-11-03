"""Read-only Microsoft Graph client. Tokens stay encrypted in the Windows user vault."""
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

GRAPH = 'https://graph.microsoft.com/v1.0'
# Broader read scope explicitly requested by the owner; no write permissions.
SCOPE = 'https://graph.microsoft.com/Files.Read https://graph.microsoft.com/Files.Read.All offline_access'

class CloudError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status=status

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

class CloudRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        safe_download(newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def safe_download(url):
    u=urllib.parse.urlsplit(url)
    host=(u.hostname or '').lower()
    suffixes=('1drv.com','1drv.ms','onedrive.com','live.com','sharepoint.com','sharepointonline.com','windows.net','microsoftpersonalcontent.com','svc.ms')
    if u.scheme!='https' or u.username or u.password or u.port not in (None,443) or not any(host==x or host.endswith('.'+x) for x in suffixes):
        raise CloudError('O OneDrive devolveu um endereço de conteúdo não reconhecido.',502)
    return url

def atomic(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_bytes(data);os.replace(tmp,path)

class Blob(ctypes.Structure):
    _fields_=[('size',wintypes.DWORD),('data',ctypes.POINTER(ctypes.c_ubyte))]

def crypt(data, decrypt=False):
    if os.name!='nt':raise CloudError('O cofre de credenciais requer Windows.',503)
    buffer=ctypes.create_string_buffer(data)
    incoming=Blob(len(data),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_ubyte)));out=Blob()
    function=ctypes.windll.crypt32.CryptUnprotectData if decrypt else ctypes.windll.crypt32.CryptProtectData
    if not function(ctypes.byref(incoming),None,None,None,None,1,ctypes.byref(out)):
        raise CloudError('Não foi possível aceder ao cofre Microsoft deste utilizador Windows.',503)
    try:return ctypes.string_at(out.data,out.size)
    finally:ctypes.windll.kernel32.LocalFree(out.data)

class OneDrive:
    def __init__(self,root):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
        self.lock=threading.RLock();self.stop=threading.Event();self.flow=None;self.error=''
        self.config=self._read('connection.json',{})
        self.tokens={}
        try:self.tokens=json.loads(crypt((self.root/'tokens.bin').read_bytes(),True))
        except FileNotFoundError:pass
        except Exception:self.error='Volte a ligar a conta Microsoft neste computador.'
        self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
        self.binary=urllib.request.build_opener(urllib.request.ProxyHandler({}),CloudRedirect())
    def _read(self,name,default):
        try:return json.loads((self.root/name).read_text(encoding='utf-8'))
        except (OSError,ValueError):return default
    def configure(self,client,tenant='common'):
        if not re.fullmatch(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}',client or '') or not re.fullmatch(r'(common|consumers|organizations|[0-9a-fA-F-]{36})',tenant or ''):
            raise CloudError('Indique um Client ID válido e common, consumers ou o Tenant ID.')
        with self.lock:
            if self.tokens or self.flow:raise CloudError('Desligue a conta antes de alterar a ligação.')
            self.config.update(client_id=client,tenant=tenant)
            atomic(self.root/'connection.json',json.dumps(self.config).encode())
    def state(self):
        with self.lock:
            flow=self.flow
            return dict(configured=bool(self.config.get('client_id')),connected=bool(self.tokens),error=self.error,
                        drive=self.config.get('drive_name',''),auth=dict(code=flow['user_code'],url=flow['verification_uri'],expires=max(0,int(flow['until']-time.time()))) if flow else None)
    def _oauth(self,endpoint,data):
        url='https://login.microsoftonline.com/'+self.config.get('tenant','common')+'/oauth2/v2.0/'+endpoint
        request=urllib.request.Request(url,urllib.parse.urlencode(data).encode(),{'Content-Type':'application/x-www-form-urlencoded'})
        try:
            with self.opener.open(request,timeout=20) as r:return json.load(r)
        except urllib.error.HTTPError as e:
            try:d=json.loads(e.read(65536))
            except Exception:d={}
            finally:e.close()
            return {'error':d.get('error','request_failed')}
        except (OSError,ValueError):raise CloudError('Não foi possível contactar a Microsoft. Tente novamente.',503)
    def connect(self):
        with self.lock:
            if not self.config.get('client_id'):raise CloudError('Configure primeiro o Client ID da aplicação Microsoft.')
            if self.tokens: return self.state()
            if self.flow and self.flow['until']>time.time():return self.state()
            d=self._oauth('devicecode',dict(client_id=self.config['client_id'],scope=SCOPE))
            if d.get('error'):raise CloudError('A Microsoft recusou o registo. Confirme o Client ID e que permite fluxos de cliente público.',403)
            if not d.get('device_code') or not d.get('user_code') or urllib.parse.urlsplit(d.get('verification_uri','')).hostname not in ('microsoft.com','www.microsoft.com','login.microsoftonline.com'):
                raise CloudError('Resposta de autorização Microsoft inválida.',502)
            d['until']=time.time()+int(d.get('expires_in',900));self.flow=d;self.error=''
            threading.Thread(target=self._poll,args=(d,),daemon=True).start()
            return self.state()
    def _poll(self,flow):
        interval=max(5,int(flow.get('interval',5)))
        while not self.stop.wait(interval):
            with self.lock:
                if self.flow is not flow:return
                if time.time()>=flow['until']:self.flow=None;self.error='O código expirou. Escolha Ligar OneDrive novamente.';return
            try:
                d=self._oauth('token',dict(client_id=self.config['client_id'],grant_type='urn:ietf:params:oauth:grant-type:device_code',device_code=flow['device_code']))
                error=d.get('error')
                if error=='authorization_pending':continue
                if error=='slow_down':interval+=5;continue
                if error:raise CloudError('A autorização não foi concluída. Verifique o registo Microsoft e tente novamente.',403)
                with self.lock:
                    if self.flow is not flow:return
                    self._save_tokens(d)
                drive=self.get('/me/drive?$select=id,name,driveType')
                with self.lock:
                    if self.flow is not flow:return
                    previous=self.config.get('drive_id')
                    if previous and previous!=drive['id']:
                        self.tokens={};(self.root/'tokens.bin').unlink(missing_ok=True)
                        raise CloudError('Esta biblioteca pertence a outra conta OneDrive. Ligue a conta original.',403)
                    self.config.update(drive_id=drive['id'],drive_name=drive.get('name','OneDrive'))
                    atomic(self.root/'connection.json',json.dumps(self.config).encode());self.flow=None
                return
            except CloudError as e:
                with self.lock:
                    if self.flow is not flow:return
                    self.flow=None;self.error=str(e);self.tokens={};(self.root/'tokens.bin').unlink(missing_ok=True)
                return
    def _save_tokens(self,d):
        if not d.get('access_token'):raise CloudError('A Microsoft não devolveu uma autorização válida.',403)
        self.tokens=dict(access_token=d['access_token'],refresh_token=d.get('refresh_token',self.tokens.get('refresh_token','')),until=time.time()+int(d.get('expires_in',3600)))
        atomic(self.root/'tokens.bin',crypt(json.dumps(self.tokens).encode()))
    def token(self):
        with self.lock:
            if not self.tokens:raise CloudError('Ligue primeiro a conta OneDrive.',401)
            if self.tokens.get('until',0)<time.time()+90:
                d=self._oauth('token',dict(client_id=self.config['client_id'],grant_type='refresh_token',refresh_token=self.tokens.get('refresh_token',''),scope=SCOPE))
                if d.get('error'):raise CloudError('A autorização Microsoft expirou. Desligue e volte a ligar a conta.',401)
                self._save_tokens(d)
            return self.tokens['access_token']
    def disconnect(self):
        with self.lock:
            self.flow=None;self.tokens={};self.error='';(self.root/'tokens.bin').unlink(missing_ok=True)
    def get(self,path):
        url=path if path.startswith('https://') else GRAPH+path
        if not url.startswith(GRAPH+'/'):raise CloudError('Página Microsoft inválida.',502)
        for attempt in range(3):
            try:
                request=urllib.request.Request(url,headers={'Authorization':'Bearer '+self.token(),'Accept':'application/json'})
                with self.opener.open(request,timeout=25) as r:
                    data=r.read(16*1024*1024+1)
                    if len(data)>16*1024*1024:raise CloudError('Página do catálogo demasiado grande.',502)
                    return json.loads(data)
            except urllib.error.HTTPError as e:
                status=e.code;retry=min(5,int(e.headers.get('Retry-After','2')) if str(e.headers.get('Retry-After','2')).isdigit() else 2);e.close()
                if status in (429,503) and attempt<2:
                    if self.stop.wait(retry):raise CloudError('Operação cancelada.',503)
                    continue
                raise CloudError('OneDrive indisponível ou sem autorização para este conteúdo (HTTP %s).'%status,502)
            except (OSError,ValueError):raise CloudError('Falha de ligação ao OneDrive. O catálogo foi preservado.',503)
    def item_path(self,drive,item):
        q=lambda s:urllib.parse.quote(str(s),safe='')
        return '/drives/'+q(drive)+'/items/'+q(item)
    def folders(self,parent='root'):
        drive=self.config.get('drive_id')
        if not drive:raise CloudError('Ligue primeiro o OneDrive.',401)
        path='/drives/'+urllib.parse.quote(drive,safe='')+('/root' if parent=='root' else '/items/'+urllib.parse.quote(parent,safe=''))+'/children?$select=id,name,folder&$top=200'
        rows=[];visited=set()
        while path:
            if path in visited or len(visited)>=1000:raise CloudError('Paginação de pastas inválida.',502)
            visited.add(path)
            d=self.get(path)
            if not isinstance(d.get('value'),list):raise CloudError('Lista de pastas inválida.',502)
            rows.extend(dict(id=i['id'],name=i['name']) for i in d['value'] if 'folder' in i)
            path=d.get('@odata.nextLink')
            if len(rows)>5000:raise CloudError('Escolha uma pasta com menos subpastas diretas.')
        return dict(drive=drive,items=sorted(rows,key=lambda i:i['name'].casefold()))
    def content_url(self,drive,item):
        # Graph may omit downloadUrl annotations when $select is used.
        d=self.get(self.item_path(drive,item))
        url=d.get('@microsoft.graph.downloadUrl')
        if not url:raise CloudError('A conta não disponibilizou uma ligação de leitura compatível. A integração precisa de validar o acesso autenticado desta conta.',502)
        return safe_download(url)
    def image_bytes(self,drive,item,original=False):
        url=None
        if original:url=self.content_url(drive,item)
        else:
            d=self.get(self.item_path(drive,item)+'/thumbnails')
            rows=d.get('value') or []
            if rows:url=(rows[0].get('large') or rows[0].get('medium') or {}).get('url')
            if not url:raise CloudError('Miniatura ainda não disponível no OneDrive.',404)
        request=urllib.request.Request(safe_download(url),headers={'User-Agent':'MediaForgeLab/1'})
        try:
            with self.binary.open(request,timeout=25) as r:
                data=r.read(32*1024*1024+1)
            if len(data)>32*1024*1024:raise CloudError('Imagem demasiado grande para esta visualização.',413)
            return data
        except (OSError,ValueError):raise CloudError('Não foi possível obter a imagem do OneDrive.',502)
    def close(self):self.stop.set()
