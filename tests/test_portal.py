import contextlib
import http.client
import io
import ipaddress
import json
import os
from pathlib import Path
import sys
import threading
import subprocess
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import PortalServer, parse_playlist, load_config
from network import firewall_script

PLAYLIST = '''\ufeff#EXTM3U
#EXTINF:-1 tvg-name="Fallback" group-title="PT, Generalistas",RTP 1
http://provider.invalid/private-user/private-secret/1.ts
#EXTINF:-1 group-title="PT",##### SEPARADOR #####
http://provider.invalid/private-user/private-secret/999.ts
#EXTINF:-1 group-title="PT",Duplicado
http://provider.invalid/private-user/private-secret/1.ts
#EXTINF:-1,Canal inseguro
javascript:bad()
#EXTINF:-1,Outro canal
#EXTGRP:Desporto
https://provider.invalid/private-user/private-secret/2.ts
'''


class PlaylistTests(unittest.TestCase):
    def test_metadata_commas_groups_dedup_and_separators(self):
        channels, stats = parse_playlist(PLAYLIST)
        self.assertEqual([c['id'] for c in channels], [1, 2])
        self.assertEqual(channels[0]['name'], 'RTP 1')
        self.assertEqual(channels[0]['group'], 'PT, Generalistas')
        self.assertEqual(channels[1]['group'], 'Desporto')
        self.assertEqual(stats, dict(entries=5, separators=1, duplicates=1, invalid=1))

    def test_plain_urls_and_injected_player_options_are_not_channels(self):
        channels, stats = parse_playlist('http://example.invalid/stray\n#EXTINF:-1,Bad\nhttp://example.invalid/a.ts atrack:2\n')
        self.assertEqual(channels, [])
        self.assertEqual(stats['invalid'], 2)

    def test_configuration_refuses_public_and_overbroad_networks(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'config.json'
            for host, network in [('0.0.0.0', '192.168.1.0/24'), ('192.168.1.240', '192.168.0.0/16'), ('8.8.8.8', '8.8.8.0/24')]:
                path.write_text(json.dumps(dict(host=host, allowed_network=network, port=8090)), encoding='utf-8')
                with self.assertRaises(ValueError):
                    load_config(path)

    @unittest.skipUnless(os.name == 'nt', 'Windows firewall helper')
    def test_generated_firewall_command_parses_before_any_elevation(self):
        import base64
        script = firewall_script(dict(host='192.168.1.240', port=8090, network=ipaddress.ip_network('192.168.1.0/24')))
        encoded = base64.b64encode(script.encode('utf-16-le')).decode('ascii')
        check = "$errors=$null; $tokens=$null; [System.Management.Automation.Language.Parser]::ParseInput([Text.Encoding]::Unicode.GetString([Convert]::FromBase64String('" + encoded + "')),[ref]$tokens,[ref]$errors) | Out-Null; if($errors.Count){exit 1}"
        result = subprocess.run(['powershell.exe', '-NoProfile', '-Command', check], capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0)
        self.assertIn('-Profile Private', script)
        self.assertIn("-RemoteAddress '192.168.1.0/24'", script)


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.channels, stats = parse_playlist(PLAYLIST)
        cfg = dict(host='127.0.0.1', port=0, network=ipaddress.ip_network('127.0.0.0/24'), switch_delay_ms=1000, player_solution='ffmpeg')
        self.server = PortalServer(cfg, self.channels, stats, 'test-control')
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={'poll_interval': .02}, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def fetch(self, path, headers=None, method='GET', body=None):
        conn = http.client.HTTPConnection(*self.server.server_address, timeout=3)
        conn.request(method, path, body=body, headers=headers or {})
        response = conn.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        conn.close()
        return result

    def test_catalog_does_not_expose_streams_and_play_is_explicit(self):
        status, headers, body = self.fetch('/api/channels')
        self.assertEqual(status, 200)
        self.assertNotIn(b'private-secret', body)
        self.assertNotIn(b'provider.invalid', body)
        self.assertEqual(len(json.loads(body)['channels']), 2)
        self.assertIn('no-store', headers['Cache-Control'])
        status, _, body = self.fetch('/api/play/1')
        self.assertEqual(status, 410)
        headers={'X-MAG-Action':self.server.action_token}
        status,_,body=self.fetch('/api/media/mag',headers,'POST',json.dumps({'owner':'fixture-mag-owner','id':'1'}))
        self.assertEqual(status,200)
        self.assertIn('/media/raw/',json.loads(body)['url'])
        self.assertNotIn(b'private-secret',body)

    def test_paged_catalog_and_favorite_csrf_token(self):
        status, _, body = self.fetch('/api/catalog?kind=tv&limit=1')
        self.assertEqual(status,200)
        self.assertEqual(len(json.loads(body)['items']),1)
        self.assertNotIn(b'private-secret',body)
        data=json.dumps({'id':'1','favorite':True})
        self.assertEqual(self.fetch('/api/favorite',method='POST',body=data)[0],403)
        _,_,body=self.fetch('/api/library')
        token=json.loads(body)['action_token']
        status,_,body=self.fetch('/api/favorite',{'X-MAG-Action':token},'POST',data)
        self.assertEqual(status,200)
        self.assertTrue(json.loads(body)['favorite'])
        _,_,body=self.fetch('/api/catalog?kind=all&favorites=1')
        self.assertEqual(json.loads(body)['total'],1)
        self.assertNotIn(b'private-secret',body)

    def test_exact_static_allowlist_hides_repository_and_playlist(self):
        self.assertEqual(self.fetch('/index.html')[0], 200)
        for path in ['/config.local.json', '/.runtime/server.json', '/../server.py', '/%2e%2e/.env', '/canais-portugueses.m3u', '/server.py']:
            status, _, body = self.fetch(path)
            self.assertEqual(status, 404)
            self.assertNotIn(b'private-secret', body)

    def test_cross_site_and_rebinding_denied(self):
        for headers in [{'Host': 'attacker.invalid'}, {'Origin': 'https://attacker.invalid'}, {'Sec-Fetch-Site': 'cross-site'}]:
            self.assertEqual(self.fetch('/api/play/1', headers)[0], 403)

    def test_public_client_denied_before_catalog(self):
        self.server.config['network'] = ipaddress.ip_network('192.168.1.0/24')
        self.server.bind_host = '192.168.1.240'
        self.assertEqual(self.fetch('/api/channels')[0], 403)

    def test_stop_requires_local_control_token_and_returns_no_secrets(self):
        self.assertEqual(self.fetch('/__stop', method='POST')[0], 403)
        status, _, body = self.fetch('/api/health')
        self.assertEqual(status, 200)
        self.assertNotIn(b'test-control', body)
        self.assertEqual(self.fetch('/__stop', {'X-MAG-Control': 'test-control'}, 'POST')[0], 200)

    def test_requests_and_sensitive_paths_are_not_logged(self):
        output = io.StringIO()
        with contextlib.redirect_stderr(output):
            self.fetch('/api/play/1?private-secret')
            self.fetch('/private-user/private-secret')
        self.assertEqual(output.getvalue(), '')

    def test_installed_tv_cors_keeps_lan_host_and_action_boundaries(self):
        self.server.tv_access.key = 'a'*64
        preflight={'Origin':'null','Access-Control-Request-Method':'POST',
                   'Access-Control-Request-Headers':'X-MAG-TV, X-MAG-Action, Content-Type'}
        code,headers,_=self.fetch('/api/media/web',preflight,'OPTIONS')
        self.assertEqual(code,204)
        self.assertEqual(headers.get('Access-Control-Allow-Origin'),'null')
        code,headers,_=self.fetch('/api/library',{'Origin':'null'})
        self.assertEqual(code,403)
        self.assertNotIn('Access-Control-Allow-Origin',headers)
        tv={'Origin':'null','X-MAG-TV':'a'*64,'Sec-Fetch-Site':'cross-site'}
        code,headers,body=self.fetch('/api/library',tv)
        self.assertEqual(code,200)
        self.assertEqual(headers['Access-Control-Allow-Origin'],'null')
        self.assertNotIn(b'private-secret',body)
        self.assertEqual(self.fetch('/api/library',dict(tv,Host='evil.invalid'))[0],403)
        self.assertEqual(self.fetch('/api/source',tv)[0],403)
        self.assertEqual(self.fetch('/api/media/web',tv,'POST','{}')[0],403)
        self.assertEqual(self.fetch('/api/media/stop',dict(tv,**{'X-MAG-Action':self.server.action_token}),'POST','{}')[0],200)
        code,_,html=self.fetch('/tv/')
        self.assertEqual(code,200)
        self.assertNotIn(b'a'*64,html)

    def test_playback_diagnostics_are_private_typed_bounded_and_persistent(self):
        from diagnostics import PlaybackDiagnostics
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'playback-diagnostics.json'
            self.server.diagnostics = PlaybackDiagnostics(path)
            row = dict(session='fixture-session',seq=1,revision=12,stage='seek_call',id='m10',target=125)
            token = {'X-MAG-Action':self.server.action_token}
            self.assertEqual(self.fetch('/api/player-diagnostics',method='POST',body=json.dumps(row))[0],403)
            self.assertEqual(self.fetch('/api/player-diagnostics',dict(token,Origin='http://other.invalid'),'POST',json.dumps(row))[0],403)
            for invalid in [dict(row,url='http://private.invalid/secret'),dict(row,stage='secret'),dict(row,target=True),dict(row,id='private-secret')]:
                self.assertEqual(self.fetch('/api/player-diagnostics',token,'POST',json.dumps(invalid))[0],400)
            self.assertEqual(self.fetch('/api/player-diagnostics',token,'POST',json.dumps(row))[0],200)
            for seq in range(2,132):
                self.server.diagnostics.append(dict(row,seq=seq))
            restored = PlaybackDiagnostics(path)
            self.assertEqual(len(restored.read()['events']),128)
            self.assertEqual(restored.read()['events'][-1]['seq'],131)
            status,_,body = self.fetch('/api/player-diagnostics')
            self.assertEqual(status,200)
            self.assertNotIn(b'private-secret',body)
            self.assertNotIn(b'private.invalid',path.read_bytes())
            self.assertEqual(self.fetch('/.runtime/playback-diagnostics.json')[0],404)

    def test_update_source_and_progress_http_permissions_and_preservation(self):
        from refresh import RefreshManager
        from test_refresh import FixtureProvider
        with tempfile.TemporaryDirectory() as folder:
            self.server.runtime=Path(folder)/'runtime'
            self.server.catalog.provider=FixtureProvider()
            self.server.updater=RefreshManager(self.server,self.server.runtime,Path(folder)/'exports')
            _,_,body=self.fetch('/api/library');token=json.loads(body)['action_token']
            headers={'X-MAG-Action':token}
            for endpoint in ('/api/refresh','/api/source','/api/progress'):
                self.assertEqual(self.fetch(endpoint,method='POST',body='{}')[0],403)
            self.assertEqual(self.fetch('/api/refresh',dict(headers,Origin='https://attacker.invalid'),'POST','{}')[0],403)
            self.server.catalog.add(dict(id='m10',provider_id='10',kind='movie',name='Film',group='PT',extension='mp4',url='http://fixture.invalid/movie/10.mp4'))
            progress=json.dumps(dict(id='m10',position=120,duration=3600,completed=False))
            self.assertEqual(self.fetch('/api/progress',headers,'POST',progress)[0],200)
            self.assertEqual(self.fetch('/api/refresh',headers,'POST','{}')[0],200)
            self.server.updater.thread.join(5)
            self.assertFalse(self.server.updater.status()['running'])
            _,_,body=self.fetch('/api/media/mag',headers,'POST',json.dumps({'owner':'fixture-mag-owner','id':'m10'}))
            self.assertEqual(json.loads(body)['progress']['position'],120)
            self.assertEqual(json.loads((self.server.runtime/'progress.json').read_text())['m10']['position'],120)
            source=json.dumps(dict(url='http://Other.invalid:9000/get.php?username=SensitiveUser&password=SensitivePassword'))
            status,_,body=self.fetch('/api/source',headers,'POST',source)
            self.assertEqual(status,200)
            self.assertNotIn(b'Sensitive',body)
            _,_,body=self.fetch('/api/source');self.assertNotIn(b'Sensitive',body)
            for endpoint in ('/.runtime/source.json','/catalogo-vod/portal-canais-completos.json','/canais-completos.m3u'):
                self.assertEqual(self.fetch(endpoint)[0],404)


if __name__ == '__main__':
    unittest.main()
