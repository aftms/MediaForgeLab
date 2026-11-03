"""Public Facebook cover metadata. No login, cookies, stream extraction or tokens."""
import io
import re
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urlsplit
from PIL import Image, ImageOps

PAGE_HOSTS=frozenset(('facebook.com','www.facebook.com','m.facebook.com','web.facebook.com','fb.watch','www.fb.watch'))

def allowed(url,image=False):
    try:
        p=urlsplit(url);host=(p.hostname or '').lower()
        if p.scheme!='https' or p.username or p.password or p.port not in (None,443):return False
        if image:return host=='fbcdn.net' or host.endswith('.fbcdn.net')
        return host in PAGE_HOSTS and not p.path.lower().startswith(('/login','/checkpoint','/dialog','/consent','/privacy/consent'))
    except ValueError:return False

class PublicRedirect(urllib.request.HTTPRedirectHandler):
    max_redirections=3
    max_repeats=1
    def __init__(self,image=False):self.image=image
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if not allowed(newurl,self.image):raise ValueError('Unsupported redirect')
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def fetch(url,limit,image=False):
    if not allowed(url,image):raise ValueError('Unsupported public URL')
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),PublicRedirect(image))
    with opener.open(urllib.request.Request(url,headers={'User-Agent':'MediaForgeLab/1.0'}),timeout=6) as response:
        data=response.read(limit+1)
    if len(data)>limit:raise ValueError('Metadata too large')
    return data

class OpenGraph(HTMLParser):
    def __init__(self):super().__init__();self.values={}
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='meta' and attrs.get('property','').startswith('og:'):
            self.values[attrs['property']]=attrs.get('content','')

def metadata(url):
    try:
        parser=OpenGraph();parser.feed(fetch(url,2_000_000).decode('utf-8','replace'));values=parser.values
        if not values.get('og:type','').startswith('video'):return {}
        title=re.sub(r'[\x00-\x1f\x7f]',' ',values.get('og:title','')).strip()[:180]
        if title.lower() in ('facebook','video','vídeo'):title=''
        result=dict(title=title,author='',thumbnail='')
        image_url=values.get('og:image','')
        if not allowed(image_url,True):return result
        with Image.open(io.BytesIO(fetch(image_url,5_000_000,True))) as original:
            if original.format not in ('JPEG','PNG','WEBP') or original.width*original.height>20_000_000:return result
            image=ImageOps.exif_transpose(original).convert('RGB')
            ratio=image.width/image.height
            # Use explicit video dimensions when the public page supplies them;
            # otherwise its video poster provides the initial framing ratio.
            try:
                width=float(values['og:video:width']);height=float(values['og:video:height'])
                if width>0 and height>0:ratio=width/height
            except (KeyError,TypeError,ValueError,ZeroDivisionError):pass
            image.thumbnail((640,640));out=io.BytesIO();image.save(out,format='PNG',optimize=True)
            result['_cover']=out.getvalue();result['aspect_ratio']=ratio if .2<=ratio<=4 else 0
        return result
    except Exception:
        # Refused/private/unavailable pages preserve the existing title/cover.
        return {}
