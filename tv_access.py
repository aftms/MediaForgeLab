"""Private installed TV access; no wildcard CORS or provider credentials."""
import hmac
import json
import secrets
from pathlib import Path

ROUTES = frozenset(('/api/personal','/api/library', '/api/health', '/api/catalog', '/api/favorites',
    '/api/favorite', '/api/continue', '/api/progress', '/api/refresh',
    '/api/media/web', '/api/media/pulse', '/api/media/stop'))


class TVAccess:
    def __init__(self, path):
        path = Path(path)
        # Only build_tv.py provisions this private file. Ordinary startup does not
        # enable installed-app access or silently replace a damaged key.
        self.key = ''
        if path.exists():
            value = json.loads(path.read_text(encoding='utf-8'))['key']
            if not isinstance(value, str) or len(value) != 64:
                raise ValueError('Invalid TV access configuration')
            self.key = value

    def authorized(self, path, headers, preflight=False):
        if not self.key or path.split('?', 1)[0] not in ROUTES:
            return False
        origin = headers.get('Origin', '')
        if len(origin) > 256 or any(ord(c) < 32 for c in origin):
            return False
        if preflight:
            requested = {h.strip().lower() for h in headers.get('Access-Control-Request-Headers', '').split(',')}
            return bool(origin and headers.get('Access-Control-Request-Method') in ('GET', 'POST')
                        and 'x-mag-tv' in requested
                        and requested <= {'x-mag-tv', 'x-mag-action', 'content-type'})
        return hmac.compare_digest(headers.get('X-MAG-TV', ''), self.key)
