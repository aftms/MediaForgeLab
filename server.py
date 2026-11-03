"""Private LAN portal. Supplier streams open only for explicit, leased playback."""
import argparse
import hmac
import ipaddress
import json
import os
import re
import secrets
import ssl
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
from media import MediaManager, MediaError
from favorite_layout import FavoriteLayout, LayoutError
from catalog import Catalog
from provider import Provider
from diagnostics import PlaybackDiagnostics
from tv_access import TVAccess
from refresh import RefreshManager, read_json, json_bytes, atomic_batch, recover

BASE = Path(__file__).resolve().parent
APP_ID = "gatewayforgelab.mag-portal.v1"
STATIC = {"/": ("index.html", "text/html"),
          "/index.html": ("index.html", "text/html"),
          "/portal.js": ("portal.js", "application/javascript"),
          "/media-tracks.js": ("media-tracks.js", "application/javascript"),
          "/boot.js": ("boot.js", "application/javascript"),
          "/portal.css": ("portal.css", "text/css")}
for asset in (BASE/'public'/'web').rglob('*'):
    if asset.is_file() and asset.suffix in ('.html','.js','.css','.png','.webmanifest'):
        mime={'.html':'text/html','.js':'application/javascript','.css':'text/css','.png':'image/png','.webmanifest':'application/manifest+json'}[asset.suffix]
        STATIC['/web/'+asset.relative_to(BASE/'public'/'web').as_posix()]=('web/'+asset.relative_to(BASE/'public'/'web').as_posix(),mime)
STATIC['/web/']=('web/index.html','text/html')
for asset in (BASE/'public'/'tv').glob('*'):
    if asset.suffix in ('.html', '.js', '.css', '.png'):
        STATIC['/tv/'+asset.name]=('tv/'+asset.name,{'.html':'text/html','.js':'application/javascript','.css':'text/css','.png':'image/png'}[asset.suffix])
STATIC['/tv/']=('tv/index.html','text/html')
STATIC.update({"/assets/"+p.name:("assets/"+p.name,"image/png")
               for p in (BASE / 'public' / 'assets').glob('*.png')})


def parse_playlist(text):
    channels, seen, pending, extgroup = [], set(), None, ""
    stats = {"entries": 0, "separators": 0, "duplicates": 0, "invalid": 0}
    for raw in text.lstrip("\ufeff").splitlines():
        line = raw.strip()
        if line.startswith("#EXTINF:"):
            stats["entries"] += 1
            # Commas inside quoted attributes are not the display-name separator.
            split = re.split(r',(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)', line, maxsplit=1)
            attrs = dict(re.findall(r'([\w-]+)="([^\"]*)"', split[0]))
            pending = {"name": split[1].strip() if len(split) > 1 else attrs.get("tvg-name", "Canal"),
                       "group": attrs.get("group-title", ""), "epg_id": attrs.get("tvg-id", "")[:200]}
            extgroup = ""
        elif line.startswith("#EXTGRP:"):
            extgroup = line[8:].strip()
        elif line and not line.startswith("#"):
            if pending is None:
                stats["invalid"] += 1
                continue
            if re.match(r"^\s*#{3,}", pending["name"]):
                stats["separators"] += 1
                pending = None
                continue
            try:
                url = urlsplit(line)
                valid = url.scheme in ("http", "https") and bool(url.hostname) and not re.search(r"[\s\x00-\x1f\x7f]", line)
            except ValueError:
                valid = False
            if not valid:
                stats["invalid"] += 1
            elif line in seen:
                stats["duplicates"] += 1
            else:
                seen.add(line)
                channels.append({"id": len(channels) + 1, "name": pending["name"][:180],
                                 "group": (pending["group"] or extgroup or "Portugal")[:120], "url": line, "epg_id":pending['epg_id']})
            pending = None
    return channels, stats


def load_config(path):
    config = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    host = ipaddress.IPv4Address(config["host"])
    network = ipaddress.IPv4Network(config["allowed_network"], strict=True)
    if not host.is_private or host.is_unspecified or host not in network or not network.is_private or network.prefixlen < 24:
        raise ValueError("A private host and a private /24 or narrower LAN are required")
    port = config["port"]
    if not isinstance(port, int) or not 1024 <= port <= 65535:
        raise ValueError("Invalid port")
    ports = [port]
    for key in ('loopback_port', 'https_port'):
        extra = config.get(key)
        if extra is not None:
            if not isinstance(extra, int) or not 1024 <= extra <= 65535 or extra in ports:
                raise ValueError('Invalid or duplicate web port')
            ports.append(extra)
    if config.get("player_solution", "ffmpeg") not in ("ffmpeg", "auto"):
        raise ValueError("Invalid player solution")
    config["switch_delay_ms"] = max(800, min(5000, int(config.get("switch_delay_ms", 1000))))
    config["player_solution"] = config.get("player_solution", "ffmpeg")
    config["network"] = network
    if config.get('provider_metadata'):
        config.setdefault('catalog_cache', str(BASE / '.runtime' / 'library.json'))
    config.setdefault('favorites_path', str(BASE / '.runtime' / 'favorites.json'))
    config.setdefault('runtime_path', str(BASE / '.runtime'))
    config.setdefault('export_dir', 'D:/Workspace/share/IPTV')
    return config


class PortalServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, config, channels, stats, control):
        self.config, self.channels, self.stats, self.control = config, channels, stats, control
        self.catalog_lock = threading.RLock()
        self.runtime = Path(config.get('runtime_path',str(BASE / '.runtime')))
        self.tv_access = TVAccess(self.runtime/'tv-access.json')
        self.diagnostics = PlaybackDiagnostics(self.runtime/'playback-diagnostics.json')
        snapshot = None
        if config.get('provider_metadata'):
            snapshot = config.pop('_snapshot',None) or read_json(self.runtime/'catalog-current.json')
        if snapshot:
            self.catalog = Catalog([],dict(config,catalog_cache=None,_playlist_media=[]))
            self.catalog.provider = Provider(snapshot['source'])
            for row in snapshot['items']:
                self.catalog.add(row)
        else:
            self.catalog = Catalog(channels, config)
        summary = {k:snapshot[k] for k in ('updated','summary')} if snapshot else None
        self.updater = RefreshManager(self,self.runtime,config.get('export_dir','D:/Workspace/share/IPTV'),snapshot_info=summary) if config.get('provider_metadata') else None
        self.progress = read_json(self.runtime/'progress.json',{}) if self.updater else {}
        if self.updater:
            self.updater.restore_progress_episodes(self.progress)
        self.action_token = secrets.token_hex(24)
        self.instance = secrets.token_hex(12)
        self.bind_host, self.scheme = config['host'], 'http'
        self.media = MediaManager(self)
        self.favorite_layout = FavoriteLayout(self.runtime/'favorite-layout.json')
        super().__init__((config["host"], config["port"]), PortalHandler)

    def server_close(self):
        self.media.close()
        super().server_close()

    def handle_error(self, request, client_address):
        # No traceback, request line, URL, headers or credentials in runtime logs.
        pass


class PortalHandler(BaseHTTPRequestHandler):
    server_version = "MAGPortal"
    sys_version = ""

    @property
    def app(self):
        return getattr(self.server, 'backend', self.server)

    def setup(self):
        self.request.settimeout(10)
        super().setup()

    def log_message(self, format, *args):
        pass

    def send_error(self, code, message=None, explain=None):
        # BaseHTTPRequestHandler errors can otherwise reflect raw input.
        self.respond(code, b"Pedido recusado", "text/plain")

    def allowed(self, preflight=False):
        try:
            ip = ipaddress.IPv4Address(self.client_address[0])
        except ValueError:
            return False
        cfg = self.app.config
        if ip not in cfg["network"] and not (ip.is_loopback and self.server.bind_host=="127.0.0.1"):
            return False
        # Reject DNS rebinding, arbitrary Host, cross-site XHR and duplicate Host.
        host = self.server.bind_host + ":" + str(self.server.server_port)
        hosts = self.headers.get_all("Host", [])
        if len(hosts) != 1 or hosts[0] != host:
            return False
        if self.app.tv_access.authorized(self.path, self.headers, preflight):
            return True
        origin = self.headers.get("Origin")
        if origin and origin != self.server.scheme+"://" + host:
            return False
        if self.headers.get("Sec-Fetch-Site") == "cross-site":
            return False
        return True

    def respond(self, status, content, mime="application/json"):
        if not isinstance(content, bytes):
            content = json.dumps(content, ensure_ascii=True, separators=(",", ":")).encode("ascii")
        self.send_response(status)
        self.send_header("Content-Type", mime + "; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "private, max-age=86400" if mime == 'image/png' else "no-store, max-age=0")
        if mime != 'image/png':
            self.send_header("Pragma", "no-cache")
        self.send_header("Connection", "close")
        if self.app.tv_access.authorized(self.path, self.headers, self.command=='OPTIONS'):
            origin = self.headers.get('Origin')
            if origin:
                self.send_header('Access-Control-Allow-Origin', origin)
                self.send_header('Vary', 'Origin')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-MAG-TV, X-MAG-Action')
                self.send_header('Access-Control-Max-Age', '300')
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; media-src 'self' blob:; worker-src 'self' blob:; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(content)
        self.close_connection = True

    def do_HEAD(self):
        self.do_GET()

    def do_OPTIONS(self):
        self.respond(204 if self.allowed(preflight=True) else 403, b'')

    def do_GET(self):
        if not self.allowed():
            if self.path.startswith('/media/hls/'):
                self.app.media.delivery['rejected'] += 1
            self.respond(403, {"error": "Acesso limitado a rede local"})
            return
        # Exact route allowlist: never expose the repository or original playlist.
        route = self.path.split("?", 1)[0]
        query = {k:v[-1] for k,v in parse_qs(urlsplit(self.path).query).items()}
        if route in STATIC:
            name, mime = STATIC[route]
            self.respond(200, (BASE / "public" / name).read_bytes(), mime)
        elif route == "/api/health":
            self.respond(200, {"app": APP_ID, "status": "ok", "instance": self.app.instance,
                               "pid": os.getpid(), "channels": self.app.catalog.counts().get('tv',0),
                               "groups": len(set(c["group"] for c in self.app.catalog.by_kind.get('tv',[]))),
                               "playlist_stats": self.app.stats, "version": 6,
                               "library": self.app.catalog.counts(), "library_status": self.app.catalog.library_status})
        elif route == '/api/library':
            self.respond(200, {'counts':self.app.catalog.counts(), 'status':self.app.catalog.library_status,
                'action_token':self.app.action_token, 'switch_delay_ms':self.app.config['switch_delay_ms'],
                'player_solution':self.app.config['player_solution'], 'media_leases':True})
        elif route == '/api/refresh':
            self.respond(200,self.app.updater.status() if self.app.updater else {'enabled':False})
        elif route == '/api/player-diagnostics':
            self.respond(200,self.app.diagnostics.read())
        elif route == '/api/source':
            self.respond(200,self.app.updater.source_info() if self.app.updater else {'configured':False})
        elif route == '/api/favorites':
            try:
                with self.app.catalog_lock:
                    result=self.app.favorite_layout.browse(self.app.catalog,query)
                self.respond(200,result)
            except LayoutError as error:
                self.respond(error.status,{'error':str(error)})
            except (ValueError,TypeError):
                self.respond(400,{'error':'Filtro invÃ¡lido.'})
            except OSError:
                self.respond(503,{'error':'NÃ£o foi possÃ­vel ler a organizaÃ§Ã£o. Os favoritos foram preservados.'})
        elif route == '/api/catalog':
            try:
                self.respond(200, self.app.catalog.browse(query))
            except (ValueError, OSError):
                self.respond(400, {'error':'Filtro ou metadados indisponiveis'})
            except Exception:
                self.respond(503, {'error':'Metadados temporariamente indisponiveis'})
        elif re.fullmatch(r'/api/epg/[a-z0-9]+', route):
            self.respond(200, self.app.catalog.epg(route.rsplit('/',1)[1]))
        elif route == "/api/channels":
            self.respond(200, {"channels": [{k: c[k] for k in ("id", "name", "group")} for c in self.app.catalog.by_kind.get('tv',[])[:1000]],
                               "switch_delay_ms": self.app.config["switch_delay_ms"],
                               "player_solution": self.app.config["player_solution"]})
        elif route.startswith('/api/play/'):
            self.respond(410, {'error':'Reinicie o portal MAG para usar o controlo de ligaÃ§Ã£o Ãºnica.'})
        elif route == '/api/media/status':
            self.respond(200,self.app.media.status())
        elif route == '/api/continue':
            items=[]
            for identifier, progress in reversed(list(self.app.progress.items())):
                if progress.get('completed') or progress.get('position',0)<10:
                    continue
                item=self.app.catalog.by_id.get(identifier)
                if item:
                    items.append(dict(self.app.catalog.public(item),progress=progress))
                if len(items)>=30:
                    break
            self.respond(200,{'items':items})
        elif route == '/web/ca.cer' and self.app.config.get('tls_ca'):
            self.respond(200,Path(self.app.config['tls_ca']).read_bytes(),'application/pkix-cert')
        elif route.startswith('/media/raw/'):
            try:
                self.app.media.serve_raw(self,route.rsplit('/',1)[1])
            except MediaError as error:
                self.respond(error.status,{'error':str(error)})
            except (OSError,ValueError):
                self.close_connection=True
        elif route.startswith('/media/hls/'):
            try:
                _,_,_,token,name=route.split('/')
                content,mime=self.app.media.segment(token,name,self.client_address[0])
                self.respond(200,content,mime)
            except MediaError as error:
                self.respond(error.status,{'error':str(error)})
            except (OSError,ValueError):
                self.respond(404,{'error':'Segmento indisponÃ­vel.'})
        else:
            self.respond(404, {"error": "Nao encontrado"})

    def do_POST(self):
        payload = b''
        if self.path in ('/api/refresh','/api/source','/api/progress','/api/favorite','/api/favorites/layout','/api/player-diagnostics','/api/media/web','/api/media/mag','/api/media/pulse','/api/media/stop'):
            try:
                size = int(self.headers.get('Content-Length','0'))
                if not 0<size<=8192:
                    raise ValueError('Body limit')
                # Consume bounded bodies before rejecting: unread TCP data can
                # turn a clear 403 into a connection reset on Windows.
                payload = self.rfile.read(size)
            except (ValueError,OSError):
                self.respond(400,{'error':'Pedido invÃ¡lido'})
                return
        if self.path == '/api/favorites/layout':
            if not self.allowed() or not hmac.compare_digest(self.headers.get('X-MAG-Action',''),self.app.action_token):
                self.respond(403,{'error':'Pedido recusado'});return
            try:
                data=json.loads(payload)
                if not isinstance(data,dict):raise ValueError()
                with self.app.catalog_lock:
                    result=self.app.favorite_layout.update(self.app.catalog,data)
                self.respond(200,result)
            except LayoutError as error:
                self.respond(error.status,{'error':str(error)})
            except (ValueError,TypeError):
                self.respond(400,{'error':'Pedido invÃ¡lido.'})
            except OSError:
                self.respond(503,{'error':'NÃ£o foi possÃ­vel guardar. A organizaÃ§Ã£o anterior foi preservada.'})
            return
        if self.path in ('/api/media/web','/api/media/mag','/api/media/pulse','/api/media/stop'):
            if not self.allowed() or not hmac.compare_digest(self.headers.get('X-MAG-Action',''),self.app.action_token):
                self.respond(403,{'error':'Pedido recusado'})
                return
            try:
                data=json.loads(payload)
                if self.path.endswith('/pulse'):
                    result=self.app.media.pulse(data,self.client_address[0])
                elif self.path.endswith('/stop'):
                    result=self.app.media.release(data,self.client_address[0])
                else:
                    mode=self.path.rsplit('/',1)[1]
                    result=self.app.media.start(data,self.client_address[0],mode)
                    if mode=='mag':
                        result['url']='http://%s:%s/media/raw/%s' % (self.app.config['host'],self.app.server_port,result['token'])
                        result['progress']=self.app.progress.get(str(data.get('id')), {})
                self.respond(200,result)
            except MediaError as error:
                self.respond(error.status,{'error':str(error)})
            except (ValueError,TypeError,KeyError):
                self.respond(400,{'error':'Pedido de reproduÃ§Ã£o invÃ¡lido.'})
            return
        if self.path == '/api/player-diagnostics':
            if not self.allowed() or not hmac.compare_digest(self.headers.get('X-MAG-Action',''),self.app.action_token):
                self.respond(403,{'error':'Pedido recusado'})
                return
            try:
                self.app.diagnostics.append(json.loads(payload))
                self.respond(200,{'saved':True})
            except (ValueError,TypeError):
                self.respond(400,{'error':'Diagnostico invalido'})
            except OSError:
                self.respond(503,{'error':'Diagnostico indisponivel'})
            return
        if self.path in ('/api/refresh','/api/source','/api/progress'):
            if not self.allowed() or not hmac.compare_digest(self.headers.get('X-MAG-Action',''),self.app.action_token):
                self.respond(403,{'error':'Pedido recusado'})
                return
            try:
                size = int(self.headers.get('Content-Length','0'))
                if not 0<size<=8192 or not self.app.updater:
                    raise ValueError('Invalid request')
                data = json.loads(payload)
                if self.path=='/api/refresh':
                    result = self.app.updater.start()
                elif self.path=='/api/source':
                    result = self.app.updater.set_source(data.get('url'))
                else:
                    identifier = str(data.get('id',''))
                    with self.app.catalog_lock:
                        item = self.app.catalog.by_id.get(identifier)
                        position = int(data.get('position',0))
                        duration = int(data.get('duration',0))
                        if not item or item['kind'] not in ('movie','episode') or not 0<=position<=604800 or not 0<=duration<=604800:
                            raise ValueError('Invalid progress')
                        updated = dict(self.app.progress)
                        updated.pop(identifier, None)
                        updated[identifier] = dict(position=position,duration=duration,completed=data.get('completed') is True)
                        atomic_batch({self.app.runtime/'progress.json':json_bytes(updated)},self.app.runtime/'progress-journal.json')
                        self.app.progress = updated
                        result = {'saved':True}
                self.respond(200,result)
            except (ValueError,TypeError,KeyError):
                self.respond(400,{'error':'Pedido invÃ¡lido ou atualizaÃ§Ã£o em curso. Verifique os dados e tente novamente.'})
            except Exception:
                self.respond(503,{'error':'NÃ£o foi possÃ­vel guardar. Os dados anteriores foram preservados.'})
            return
        if self.path == '/api/favorite':
            if not self.allowed() or not hmac.compare_digest(self.headers.get('X-MAG-Action',''), self.app.action_token):
                self.respond(403, {'error':'Pedido recusado'})
                return
            try:
                size = int(self.headers.get('Content-Length','0'))
                if not 0 < size <= 2048:
                    raise ValueError('Size')
                data = json.loads(payload)
                if not isinstance(data.get('favorite'), bool):
                    raise ValueError('Favorite flag')
                with self.app.catalog_lock:
                    result = self.app.catalog.favorite(str(data.get('id','')), data['favorite'])
                self.respond(200,result)
            except (ValueError, KeyError, TypeError):
                self.respond(400, {'error':'Pedido invalido'})
            except OSError:
                self.respond(503, {'error':'Nao foi possivel guardar o favorito'})
            return
        token = self.headers.get("X-MAG-Control", "")
        if (self.path != "/__stop" or not self.allowed()
                or self.client_address[0] not in (self.app.config["host"],"127.0.0.1")
                or not hmac.compare_digest(token, self.app.control)):
            self.respond(403, {"error": "Pedido recusado"})
            return
        self.respond(200, {"stopping": True})
        threading.Thread(target=self.app.shutdown, daemon=True).start()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(BASE / "config.local.json"))
    args = parser.parse_args()
    runtime = BASE / ".runtime"
    state = runtime / "server.json"
    server = None
    listeners = []
    try:
        config = load_config(args.config)
        for journal in ('update','episode','source','status','progress'):
            recover(Path(config['runtime_path'])/(journal+'-journal.json'))
        state = Path(config.get('state_path', str(state)))
        print('Media Forge Lab: a ler catalogo guardado',flush=True)
        config['_snapshot'] = read_json(Path(config['runtime_path'])/'catalog-current.json') if config.get('provider_metadata') else None
        channels, stats = [], {'source':'validated_snapshot'}
        config['_playlist_media'] = []
        if not config['_snapshot']:
            playlist = Path(config["playlist"])
            if playlist.stat().st_size > 64 * 1024 * 1024:
                raise ValueError("Playlist too large")
            channels, stats = parse_playlist(playlist.read_text(encoding="utf-8-sig", errors="replace"))
            if not channels:
                raise ValueError("No valid channels")
            if config.get('movies_playlist'):
                movies, movie_stats = parse_playlist(Path(config['movies_playlist']).read_text(encoding='utf-8-sig', errors='replace'))
                stats['movie_entries'] = movie_stats['entries']
                for movie in movies:
                    pid = Path(urlsplit(movie['url']).path).stem
                    if pid.isdigit():
                        movie.update(id='m'+pid, provider_id=pid, kind='movie', country='')
                        config['_playlist_media'].append(movie)
        print('Media Forge Lab: a criar indices da biblioteca',flush=True)
        server = PortalServer(config, channels, stats, secrets.token_hex(32))
        print('Media Forge Lab: servidor HTTP pronto',flush=True)
        for address,port,scheme in [('127.0.0.1',config.get('loopback_port'),'http'),(config['host'],config.get('https_port'),'https')]:
            if not port:
                continue
            listener=ThreadingHTTPServer((address,port),PortalHandler)
            listener.backend,listener.bind_host,listener.scheme=server,address,scheme
            listener.handle_error=lambda *args: None
            if scheme=='https':
                context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                # truststore's client wrapper verifies a peer even on a listening socket.
                # Use its native context only for inbound TLS; outgoing verification stays intact.
                context.minimum_version=ssl.TLSVersion.TLSv1_2
                context.load_cert_chain(config['tls_cert'],config['tls_key'])
                if 'truststore' in type(context).__module__:
                    context=context._ctx
                listener.socket=context.wrap_socket(listener.socket,server_side=True)
            listeners.append(listener)
            threading.Thread(target=listener.serve_forever,daemon=True).start()
        runtime.mkdir(exist_ok=True)
        state.write_text(json.dumps({"pid": os.getpid(), "instance": server.instance,
                                    "url": "http://%s:%s" % server.server_address,
                                    "control": server.control}), encoding="utf-8")
        (runtime/'startup-error.txt').unlink(missing_ok=True)
        print('Media Forge Lab: HTTP e HTTPS prontos',flush=True)
        server.serve_forever(poll_interval=0.25)
        return 0
    except Exception as error:
        runtime.mkdir(exist_ok=True)
        # Type only: filesystem exceptions / M3U parse errors may contain secrets.
        (runtime / "startup-error.txt").write_text("Falha no arranque: " + type(error).__name__, encoding="utf-8")
        return 1
    finally:
        for listener in listeners:
            listener.shutdown()
            listener.server_close()
        if server is not None:
            server.server_close()
            try:
                if json.loads(state.read_text(encoding="utf-8"))["instance"] == server.instance:
                    state.unlink()
            except (OSError, ValueError, KeyError):
                pass


if __name__ == "__main__":
    raise SystemExit(main())
