import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tv_access import TVAccess


class TVAccessTests(unittest.TestCase):
    def test_access_is_opt_in_and_requires_private_key_on_actual_request(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'tv.json'
            self.assertFalse(TVAccess(path).authorized('/api/library',{'Origin':'null'}))
            path.write_text(json.dumps({'key':'a'*64}))
            access=TVAccess(path)
            for origin in ('null','file://','http://installed-widget.local'):
                self.assertFalse(access.authorized('/api/library',{'Origin':origin}))
                self.assertFalse(access.authorized('/api/library',{'Origin':origin,'X-MAG-TV':'b'*64}))
                self.assertTrue(access.authorized('/api/library',{'Origin':origin,'X-MAG-TV':'a'*64}))
            for route in ('/__stop','/api/source','/web/','/.runtime/tv-access.json','/api/media/mag'):
                self.assertFalse(access.authorized(route,{'X-MAG-TV':'a'*64}))

    def test_preflight_grants_no_actual_access_and_restricts_methods_headers(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'tv.json';path.write_text(json.dumps({'key':'a'*64}));access=TVAccess(path)
            headers={'Origin':'null','Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'x-mag-tv, content-type, x-mag-action'}
            self.assertTrue(access.authorized('/api/media/web',headers,True))
            self.assertFalse(access.authorized('/api/media/web',headers))
            headers['Access-Control-Request-Method']='DELETE'
            self.assertFalse(access.authorized('/api/media/web',headers,True))
            headers['Access-Control-Request-Method']='POST';headers['Access-Control-Request-Headers']+=' , x-mag-control'
            self.assertFalse(access.authorized('/api/media/web',headers,True))

    def test_corrupt_configuration_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'tv.json';path.write_text('{"key":""}')
            with self.assertRaises(ValueError):TVAccess(path)
