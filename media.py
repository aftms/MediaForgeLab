"""One household playback lease, private upstream proxy and bounded HLS output."""
import json
from collections import OrderedDict
import os
from pathlib import Path
import re
import secrets
import shutil
import socket
import subprocess
import threading
import time
import urllib.request
import urllib.error


class MediaError(Exception):
    def __init__(self, message, status=409):
        super().__init__(message)
        self.status = status


def process_options():
    keep = ('SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'LOCALAPPDATA', 'PATH')
    return dict(stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                env={k: os.environ[k] for k in keep if k in os.environ})


class MediaManager:
    def __init__(self, app):
        self.app = app
        self.lock = threading.RLock()
        self.upstream_lock = threading.Lock()
        self.forwarder = None
        self.session = None
        self.last_failure = None
        self.requests = {}
        self.probe_cache = OrderedDict()
        self.delivery = {'playlists':0, 'segments':0, 'rejected':0}
        self.closed = threading.Event()
        self.root = app.runtime / 'media'
        self.ffmpeg = app.config.get('ffmpeg') or shutil.which('ffmpeg')
        self.ffprobe = app.config.get('ffprobe') or shutil.which('ffprobe')
        self.thread = threading.Thread(target=self._reap, daemon=True)
        self.thread.start()

    def _reap(self):
        while not self.closed.wait(5):
            with self.lock:
                if self.session and time.monotonic() - self.session['seen'] > 120:
                    self._stop()

    def _cancel_forwarder(self, forwarder):
        # Called under self.lock. A single FFmpeg may open the next HTTP range
        # before closing the previous one. End both sockets before releasing the
        # upstream lock, so the next range never creates a second supplier stream.
        forwarder['cancelled'] = True
        for key in ('client','upstream'):
            connection = forwarder.get(key)
            if connection:
                try:connection.shutdown(socket.SHUT_RDWR)
                except OSError:pass

    def _stop(self):
        session, self.session = self.session, None
        if not session:
            return
        if self.forwarder and self.forwarder['session'] is session:
            self._cancel_forwarder(self.forwarder)
        for key in ('probe_process', 'process'):
            proc = session.get(key)
            if proc and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=4)
        folder = self.root / session['token']
        if folder.parent.resolve() == self.root.resolve() and folder.exists():
            shutil.rmtree(folder, ignore_errors=True)

    def close(self):
        self.closed.set()
        with self.lock:
            self._stop()

    def status(self):
        with self.lock:
            s = self.session
            return dict(active=bool(s), device=s.get('device', 'MAG' if s['mode']=='mag' else 'Navegador') if s else None,
                        state=s['state'] if s else 'idle', delivery=dict(self.delivery),
                        startup_ms=dict(s.get('startup_ms',{})) if s else {}, stage=s.get('stage') if s else None)

    def _get(self, token, ip=None, touch=True):
        s = self.session
        if not s or not secrets.compare_digest(s['token'], str(token)) or (ip and s['ip'] != ip):
            raise MediaError('Esta sessão de reprodução terminou.', 410)
        if touch:
            s['seen'] = time.monotonic()
        return s

    def start(self, data, ip, mode):
        owner = str(data.get('owner', ''))
        if not re.fullmatch(r'[A-Za-z0-9_-]{12,100}', owner):
            raise MediaError('Identificação do leitor inválida.', 400)
        identifier = str(data.get('id', ''))
        item = self.app.catalog.by_id.get(identifier)
        if not item or item['kind'] not in ('tv','movie','episode'):
            raise MediaError('Conteúdo indisponível. Abra a série antes do episódio.', 404)
        try:
            resume = self.app.progress.get(identifier, {})
            position = float(data.get('position', resume.get('position',0) if not resume.get('completed') else 0))
            audio_index = int(data.get('audio',0))
            if not 0 <= position <= 604800 or not 0 <= audio_index <= 100:
                raise ValueError()
        except (ValueError, TypeError, OverflowError):
            raise MediaError('Posição ou faixa de áudio inválida.', 400) from None
        with self.lock:
            request_id = int(data.get('request_id') or 0)
            if request_id and request_id <= self.requests.get((owner, ip), 0):
                raise MediaError('Este pedido de reprodução foi substituído ou cancelado.', 410)
            if self.session:
                if (self.session['owner'], self.session['ip'], self.session['mode']) != (owner, ip, mode):
                    raise MediaError('Já existe uma reprodução ativa. Pare-a no outro dispositivo para continuar.')
                self._stop()
            if request_id:
                self._remember_request(owner, ip, request_id)
            token = secrets.token_hex(24)
            s = dict(token=token, owner=owner, ip=ip, mode=mode, id=identifier, kind=item['kind'], request_id=request_id,
                     seen=time.monotonic(), started=time.monotonic(), startup_ms={}, state='ready' if mode=='mag' else 'preparing',
                     stage='ready' if mode=='mag' else 'source', url=self.app.catalog.play_url(identifier), position=position if item['kind']!='tv' else 0,
                     duration=0, audio=[], compatibility=bool(data.get('compatibility')), audio_index=audio_index)
            if mode == 'web':
                s['device'] = {'samsung':'Samsung TV','androidtv':'Android TV','tv':'TV'}.get(data.get('device'), 'Navegador')
            self.last_failure = None
            self.delivery = {'playlists':0, 'segments':0, 'rejected':0}
            self.session = s
            if mode == 'web':
                if not self.ffmpeg or not self.ffprobe or not self.app.config.get('loopback_port'):
                    self.session = None
                    raise MediaError('O leitor web precisa de FFmpeg e do serviço local.', 503)
                threading.Thread(target=self._prepare, args=(s,), daemon=True).start()
            return self._public(s)

    def _public(self, s):
        return {k:s[k] for k in ('token','id','kind','state','position','duration','audio','stage')}

    def pulse(self, data, ip):
        with self.lock:
            if self.last_failure == (data.get('token'), ip):
                raise MediaError('Não foi possível abrir este conteúdo no fornecedor ou preparar o vídeo. A ligação foi libertada; pode tentar outro título.', 503)
            s = self._get(data.get('token'), ip)
            result = self._public(s)
            if s.get('error'):
                result['error'] = s['error']
            if s['mode']=='web':
                result['url'] = '/media/hls/'+s['token']+'/index.m3u8'
                result['video_mode'] = s.get('video_mode')
            return result

    def release(self, data, ip):
        with self.lock:
            request_id = int(data.get('request_id') or 0)
            if request_id and data.get('owner'):
                self._remember_request(str(data['owner']), ip, request_id)
                if self.session and (self.session['owner'], self.session['ip'], self.session['request_id']) != (data['owner'], ip, request_id):
                    return {'stopped':True}
            if not self.session:
                return {'stopped':True}
            if not data.get('token') and self.session['owner']==data.get('owner') and self.session['ip']==ip:
                data=dict(data,token=self.session['token'])
            self._get(data.get('token'), ip)
            self._stop()
            return {'stopped': True}

    def _remember_request(self, owner, ip, number):
        key = (owner, ip)
        self.requests[key] = max(number, self.requests.get(key, 0))
        if len(self.requests) > 128:
            self.requests.pop(next(iter(self.requests)))

    def _prepare(self, s):
        try:
            raw = 'http://127.0.0.1:%s/media/raw/%s' % (self.app.config['loopback_port'], s['token'])
            fast_tv = s['kind']=='tv' and s.get('device') in ('Samsung TV','Android TV') and not s['compatibility']
            android_live = fast_tv and s.get('device')=='Android TV'
            browser_vod = s['kind'] in ('movie','episode') and s.get('device')=='Navegador' and not s['compatibility']
            info = {'streams':[], 'format':{}}
            cache_key = (s['id'], s['url'])
            with self.lock:
                if self.session is not s:
                    return
                cached = self.probe_cache.get(cache_key) if s['kind'] != 'tv' and not s['compatibility'] else None
                if cached and cached[0] > time.monotonic():
                    info = cached[1]
                    self.probe_cache.move_to_end(cache_key)
                    s['startup_ms']['probe_cached'] = 1
                else:
                    cached = None
            if not cached and not fast_tv:
                with self.lock:
                    if self.session is not s:
                        return
                    s['stage'] = 'analysis'
                    proc = subprocess.Popen([self.ffprobe,'-v','quiet','-rw_timeout','15000000',
                        '-analyzeduration','4000000','-probesize','4000000','-show_streams','-show_format','-of','json',raw],
                        stdout=subprocess.PIPE, **process_options())
                    s['probe_process'] = proc
                output, _ = proc.communicate(timeout=25)
                if proc.returncode:
                    raise ValueError('probe')
                info = json.loads(output)
                with self.lock:
                    if self.session is not s:
                        return
                    s['startup_ms']['probe_ready'] = round((time.monotonic()-s['started'])*1000)
                    if s['kind'] != 'tv' and any(v.get('codec_type')=='video' and v.get('codec_name') for v in info.get('streams',[])):
                        # Bounded metadata only, never video. Changed source URL misses
                        # the cache; compatibility always performs a fresh full probe.
                        self.probe_cache[cache_key] = (time.monotonic()+3600, info)
                        self.probe_cache.move_to_end(cache_key)
                        while len(self.probe_cache)>128:
                            self.probe_cache.popitem(last=False)
            videos = [v for v in info.get('streams',[]) if v.get('codec_type')=='video']
            audio = [v for v in info.get('streams',[]) if v.get('codec_type')=='audio']
            if not fast_tv and not videos:
                raise ValueError('video')
            # Native TV decoders receive original video in HLS without a separate
            # upstream probe. Compatibility mode retains full analysis/transcode.
            copy_video = fast_tv or (videos[0].get('codec_name')=='h264' and videos[0].get('pix_fmt') in ('yuv420p','yuvj420p') and not s['compatibility'])
            folder = self.root / s['token']
            with self.lock:
                if self.session is not s:
                    return
                folder.mkdir(parents=True, exist_ok=True)
                s['duration'] = float(info.get('format',{}).get('duration') or 0)
                s['audio'] = [dict(index=i,language=a.get('tags',{}).get('language',''),codec=a.get('codec_name','')) for i,a in enumerate(audio)]
                ai = max(0, min(len(audio)-1, s['audio_index']))
                command = [self.ffmpeg,'-hide_banner','-loglevel','quiet','-nostdin','-y','-rw_timeout','15000000']
                # Android live input needs only enough analysis to identify its tracks.
                # Keep keyframe-aligned segments and original video; other clients
                # and compatibility mode retain the established full analysis.
                if android_live:
                    command += ['-analyzeduration','1000000','-probesize','1500000']
                elif browser_vod:
                    # The preceding probe already identified codecs and tracks.
                    command += ['-analyzeduration','1000000','-probesize','2000000']
                if s['position']:
                    command += ['-ss',str(s['position'])]
                command += ['-readrate','1','-readrate_initial_burst','12','-i',raw,'-map','0:v:0','-map','0:a:%d?'%ai,'-sn','-dn']
                command += ['-c:v','copy'] if copy_video else ['-c:v','libx264','-preset','veryfast','-crf','22','-pix_fmt','yuv420p','-g','48','-sc_threshold','0']
                command += ['-c:a','copy'] if (fast_tv and s.get('device')=='Samsung TV') or (audio and audio[ai].get('codec_name')=='aac') else ['-c:a','aac','-b:a','160k','-ac','2']
                command += ['-f','hls','-hls_time','2' if android_live or browser_vod else '4','-hls_list_size','10','-hls_delete_threshold','2',
                    '-hls_flags','delete_segments+temp_file','-hls_segment_filename',str(folder/'s%06d.ts'),str(folder/'index.m3u8')]
                s['video_mode'] = 'remux' if copy_video else 'transcode'
                s['stage'] = s['video_mode']
                s['startup_ms']['processing_started'] = round((time.monotonic()-s['started'])*1000)
                s['process'] = subprocess.Popen(command, stdout=subprocess.DEVNULL, **process_options())
            for _ in range(160):
                with self.lock:
                    if self.session is not s:
                        return
                    if (folder/'index.m3u8').exists():
                        s['state']='ready'
                        s['stage']='ready'
                        s['startup_ms']['playlist_ready']=round((time.monotonic()-s['started'])*1000)
                        return
                    if s['process'].poll() is not None:
                        raise ValueError('media')
                time.sleep(.25)
            raise ValueError('timeout')
        except Exception:
            with self.lock:
                if self.session is s:
                    self._stop()
                    self.last_failure = (s['token'], s['ip'])
            # No exception/URL/process arguments are written to logs.

    def serve_raw(self, handler, token):
        with self.lock:
            s = self._get(token, touch=False)
            ip = handler.client_address[0]
            if s['mode']=='web' and ip!='127.0.0.1' or s['mode']=='mag' and ip!=s['ip']:
                raise MediaError('Pedido recusado.',403)
            url = s['url']
            s['startup_ms'].setdefault('proxy_request',round((time.monotonic()-s['started'])*1000))
            s['startup_ms']['source_requests']=s['startup_ms'].get('source_requests',0)+1
            s['startup_ms']['last_proxy_request']=round((time.monotonic()-s['started'])*1000)
            if s['mode']=='web' and self.forwarder and self.forwarder['session'] is s:
                self._cancel_forwarder(self.forwarder)
        if not self.upstream_lock.acquire(timeout=12):
            raise MediaError('A ligação anterior ainda está a terminar.',409)
        forwarder = None
        try:
            with self.lock:
                self._get(token, touch=s['mode']=='mag')
                forwarder = dict(session=s,client=handler.connection,upstream=None,cancelled=False)
                self.forwarder = forwarder
            headers={'User-Agent':'MagForgeLab/1','Connection':'close'}
            byte_range=handler.headers.get('Range')
            if byte_range and re.fullmatch(r'bytes=\d*-\d*',byte_range):
                headers['Range']=byte_range
            opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
            try:
                s['startup_ms'].setdefault('upstream_open',round((time.monotonic()-s['started'])*1000))
                s['startup_ms']['last_upstream_open']=round((time.monotonic()-s['started'])*1000)
                response=opener.open(urllib.request.Request(url,headers=headers,method='HEAD' if handler.command=='HEAD' else 'GET'),timeout=10)
                s['startup_ms'].setdefault('upstream_headers',round((time.monotonic()-s['started'])*1000))
                s['startup_ms']['last_upstream_headers']=round((time.monotonic()-s['started'])*1000)
            except urllib.error.HTTPError as error:
                handler.respond(502,{'error':'O fornecedor não disponibilizou este conteúdo.'})
                error.close()
                return
            with response:
                with self.lock:
                    # CPython HTTPResponse exposes its transport through SocketIO.
                    forwarder['upstream'] = getattr(getattr(response.fp,'raw',None),'_sock',None)
                    if forwarder['cancelled'] or self.session is not s:
                        self._cancel_forwarder(forwarder)
                        return
                handler.send_response(response.status)
                for name in ('Content-Length','Content-Range','Accept-Ranges','Content-Type'):
                    value=response.headers.get(name)
                    if value:
                        handler.send_header(name,value)
                handler.send_header('Cache-Control','no-store')
                handler.send_header('Connection','close')
                handler.end_headers()
                handler.close_connection=True
                if handler.command=='HEAD':
                    return
                while True:
                    with self.lock:
                        if self.session is not s or forwarder['cancelled']:
                            break
                        # FFmpeg traffic is not a browser heartbeat. A crashed
                        # browser must release even a continuously running TV feed.
                        self._get(token, touch=s['mode']=='mag')
                    # Forward available bytes immediately. read(n) waits to fill n and
                    # can add seconds of latency to sparse/live upstream packets.
                    chunk=response.read1(64*1024)
                    if not chunk:
                        break
                    s['startup_ms'].setdefault('first_bytes',round((time.monotonic()-s['started'])*1000))
                    handler.wfile.write(chunk)
        finally:
            with self.lock:
                if self.forwarder is forwarder:
                    self.forwarder = None
            s['startup_ms']['last_upstream_closed']=round((time.monotonic()-s['started'])*1000)
            self.upstream_lock.release()

    def segment(self, token, name, ip):
        with self.lock:
            try:s=self._get(token,ip)
            except MediaError:
                self.delivery['rejected'] += 1
                raise
            if s['mode']!='web' or not re.fullmatch(r'index\.m3u8|s\d+\.ts',name):
                raise MediaError('Não encontrado.',404)
            path=self.root/token/name
            if not path.is_file():
                raise MediaError('A preparar vídeo.',404)
            self.delivery['playlists' if name.endswith('.m3u8') else 'segments'] += 1
            return path.read_bytes(), 'application/vnd.apple.mpegurl' if name.endswith('.m3u8') else 'video/mp2t'
