"""Bounded, read-only Xtream metadata. Credentials stay in memory from the M3U."""
import base64
import gzip
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request

ACTIONS = {'get_live_categories', 'get_live_streams', 'get_vod_categories', 'get_vod_streams', 'get_series_categories', 'get_series', 'get_series_info', 'get_short_epg'}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Provider:
    def __init__(self, url):
        parsed = urllib.parse.urlsplit(url)
        parts = parsed.path.strip('/').split('/')
        if (parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.fragment
                or re.search(r'[\s\x00-\x1f\x7f]', url)):
            raise ValueError('Unsupported playlist source')
        parsed.port  # Validate the port without normalizing the original authority.
        self.origin = parsed.scheme + '://' + parsed.netloc
        if parsed.path == '/get.php':
            query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
            if any(len(query.get(key, [])) != 1 or not query[key][0] for key in ('username','password')):
                raise ValueError('Invalid source credentials')
            self.user, self.password = query['username'][0], query['password'][0]
        elif len(parts) == 4 and parts[0] in ('live', 'movie', 'series'):
            self.user, self.password = [urllib.parse.unquote(p) for p in parts[1:3]]
        else:
            raise ValueError('Unsupported playlist source')
        if not self.user or not self.password:
            raise ValueError('Empty credentials')
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def fetch(self, action, timeout=30, **parameters):
        if action not in ACTIONS or any(k not in ('category_id', 'stream_id', 'series_id', 'limit') or not str(v).isdigit() for k, v in parameters.items()):
            raise ValueError('Unsupported metadata operation')
        query = dict(username=self.user, password=self.password, action=action, **parameters)
        url = self.origin + '/player_api.php?' + urllib.parse.urlencode(query)
        req = urllib.request.Request(url, headers={'User-Agent': 'MAG-Local-Portal/2', 'Accept-Encoding': 'gzip', 'Accept': 'application/json'})
        with self.opener.open(req, timeout=max(1,min(30,float(timeout)))) as response:
            if response.status != 200:
                raise ValueError('Metadata unavailable')
            stream = gzip.GzipFile(fileobj=response) if response.headers.get('Content-Encoding') == 'gzip' else response
            data = stream.read(160 * 1024 * 1024 + 1)
            if len(data) > 160 * 1024 * 1024:
                raise ValueError('Metadata limit')
        return json.loads(data.decode('utf-8-sig'))

    def media_url(self, kind, identifier, extension='ts'):
        if kind not in ('live', 'movie', 'series') or not str(identifier).isdigit() or not re.fullmatch(r'[a-zA-Z0-9]{1,8}', extension):
            raise ValueError('Invalid media descriptor')
        return '%s/%s/%s/%s/%s.%s' % (self.origin, kind, urllib.parse.quote(self.user, safe=''), urllib.parse.quote(self.password, safe=''), identifier, extension)

    def source_url(self):
        return self.origin + '/get.php?' + urllib.parse.urlencode(dict(username=self.user, password=self.password, type='m3u_plus', output='ts'))


def decode_epg(value):
    text = str(value or '')
    try:
        decoded = base64.b64decode(text, validate=True).decode('utf-8')
        if decoded and all(c.isprintable() or c in '\n\t\r' for c in decoded):
            return decoded[:2000]
    except (ValueError, UnicodeError):
        pass
    return text[:2000]


def import_library(provider, progress=print):
    result = {'updated': int(time.time()), 'movies': [], 'series': [], 'status': {}}
    for kind, category_action, list_action in [('movies', 'get_vod_categories', 'get_vod_streams'), ('series', 'get_series_categories', 'get_series')]:
        progress('A obter metadados: ' + kind)
        try:
            categories = provider.fetch(category_action)
            category_map = {str(c.get('category_id')): str(c.get('category_name', 'Outros'))[:150] for c in categories if isinstance(c, dict)}
            rows = provider.fetch(list_action)
            if not isinstance(rows, list):
                raise ValueError('Invalid metadata list')
            seen = set()
            for row in rows:
                identifier = str(row.get('stream_id' if kind == 'movies' else 'series_id', ''))
                if not identifier.isdigit() or identifier in seen:
                    continue
                seen.add(identifier)
                result[kind].append({'id': ('m' if kind == 'movies' else 's') + identifier,
                    'provider_id': identifier, 'kind': 'movie' if kind == 'movies' else 'series',
                    'name': str(row.get('name') or 'Sem titulo')[:180],
                    'group': category_map.get(str(row.get('category_id')), 'Outros'),
                    'extension': str(row.get('container_extension') or 'mp4')[:8],
                    'plot': str(row.get('plot') or '')[:1500], 'year': str(row.get('year') or row.get('releaseDate') or '')[:10]})
            result['status'][kind] = 'ok'
            progress(kind + ': ' + str(len(result[kind])) + ' titulos')
        except Exception as error:
            # Exception text/URL can contain authentication; only store the type.
            result['status'][kind] = type(error).__name__
            progress(kind + ': metadados indisponiveis (' + type(error).__name__ + ')')
    return result
