import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image
from personal import PersonalLibrary, PersonalMedia, identifier
from onedrive import CloudError, OneDrive, crypt, safe_download
from types import SimpleNamespace

class FakeCloud:
    def __init__(self):
        self.config={'drive_id':'drive'};self.fail=False;self.rows=[
            {'id':'photo','name':'Foto 100%.jpg','image':{'width':160,'height':90},'file':{'mimeType':'image/jpeg'},'photo':{'takenDateTime':'2020-05-01T00:00:00Z'},'eTag':'a'},
            {'id':'video','name':'Video.mp4','video':{'duration':100000,'width':160,'height':90},'eTag':'a'}]
        self.calls=[];self.connected=True
    def state(self):return {'connected':self.connected,'configured':True}
    def close(self):pass
    def item_path(self,drive,item):return '/drives/'+drive+'/items/'+item
    def get(self,path):
        self.calls.append(path)
        if self.fail:raise CloudError('Falha simulada',503)
        if '/children' in path:return {'value':self.rows}
        return {'id':'root','name':'Piloto','folder':{}}
    def content_url(self,drive,item):return 'https://fixture.1drv.com/'+item
    def image_bytes(self,drive,item,original=False):
        out=io.BytesIO();Image.new('RGB',(160,90),'teal').save(out,'JPEG');return out.getvalue()

class PersonalTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.cloud=FakeCloud();self.library=PersonalLibrary(self.temp.name,self.cloud)
        self.library.add_root('root');self.roots=[dict(r) for r in self.library.db.execute('SELECT * FROM roots')]
        self.library._scan(self.roots)
    def tearDown(self):self.library.close();self.temp.cleanup()
    def test_scan_preserves_organization_and_partial_failure(self):
        photo=identifier('drive','photo');video=identifier('drive','video')
        self.library.update({'operation':'favorite','id':photo,'favorite':True})
        album=self.library.update({'operation':'album-create','name':'Férias'})['id']
        self.library.update({'operation':'album-add','album':album,'id':photo})
        self.library.update({'operation':'progress','id':video,'position':25,'duration':100})
        self.cloud.rows[0]['name']='Nova foto.jpg';self.cloud.rows[0]['eTag']='b'
        self.library._scan(self.roots);self.library._scan(self.roots)
        self.assertEqual(self.library.browse({})['total'],2)
        self.assertTrue(self.library.get(photo)['favorite'])
        self.assertEqual(self.library.browse({'album':album})['items'][0]['name'],'Nova foto.jpg')
        self.assertEqual(self.library.get(video)['position'],25)
        self.cloud.fail=True;self.library._scan(self.roots)
        self.assertEqual(self.library.browse({})['total'],2)
        self.assertTrue(self.library.scan['error'])
        self.cloud.fail=False;self.cloud.rows=[];self.library._scan(self.roots)
        self.assertEqual(self.library.browse({})['total'],2)
        self.assertFalse(any('content' in p for p in self.cloud.calls))
    def test_changing_folder_or_repeated_page_preserves_catalog(self):
        original=self.cloud.get
        tags=iter(['before','after'])
        def changing(path):
            if 'cTag' in path:return {'cTag':next(tags)}
            return original(path)
        with patch.object(self.cloud,'get',changing):self.library._scan(self.roots)
        self.assertTrue(self.library.scan['error'])
        self.assertEqual(self.library.browse({})['total'],2)
        def repeated(path):
            if '/children' in path:return {'value':self.cloud.rows,'@odata.nextLink':path}
            return original(path)
        with patch.object(self.cloud,'get',repeated):self.library._scan(self.roots)
        self.assertIn('Paginação',self.library.scan['error'])
        self.assertEqual(self.library.browse({})['total'],2)

    def test_filters_literal_search_anchor_and_photos(self):
        self.assertEqual(self.library.browse({'kind':'photo','year':'2020'})['total'],1)
        self.assertEqual(self.library.browse({'q':'100%'})['total'],1)
        self.assertEqual(self.library.browse({'q':'_missing'})['total'],0)
        self.assertEqual(self.library.browse({'kind':'video','continue':'1'})['total'],0)
        id=identifier('drive','photo')
        result=self.library.browse({'kind':'photo','anchor':id,'limit':'1'})
        self.assertEqual(result['items'][0]['id'],id)
        self.assertNotIn('remote',result['items'][0]);self.assertNotIn('drive',result['items'][0])
        data=self.library.image(id,True)
        self.assertEqual(Image.open(io.BytesIO(data)).format,'JPEG')
        self.cloud.connected=False
        with self.assertRaises(CloudError):self.library.image(id,True)
    def test_album_changes_do_not_touch_cloud(self):
        calls=list(self.cloud.calls);id=identifier('drive','photo')
        a=self.library.update({'operation':'album-create','name':'Viagem'})['id']
        self.library.update({'operation':'album-add','album':a,'id':id})
        self.library.update({'operation':'album-add','album':a,'id':id})
        self.assertEqual(self.library.browse({'album':a})['total'],1)
        self.library.update({'operation':'album-rename','id':a,'name':'Verão'})
        self.library.update({'operation':'album-delete','id':a})
        self.assertEqual(self.library.browse({})['total'],2)
        self.assertEqual(self.cloud.calls,calls)
    def test_personal_lease_excludes_another_personal_device(self):
        app=SimpleNamespace(config={'ffmpeg':'fixture','ffprobe':'fixture','loopback_port':1})
        m=PersonalMedia(app,self.library)
        try:
            with patch.object(m,'_prepare',lambda s:None):
                p=m.start({'id':identifier('drive','video'),'owner':'personal-browser-1'},'192.168.1.5','web')
                from media import MediaError
                with self.assertRaises(MediaError):m.start({'id':identifier('drive','video'),'owner':'personal-browser-2'},'192.168.1.6','web')
                m.session['state']='ready';m.session.update(video_mode='remux',duration=100,audio=[])
                self.assertTrue(m.pulse(p,'192.168.1.5')['url'].startswith('/personal/hls/'))
                m.release(p,'192.168.1.5')
                self.assertFalse(m.status()['active'])
        finally:m.close()
    def test_cloud_redirect_and_graph_boundaries(self):
        for url in ['http://fixture.1drv.com/a','https://evil.invalid/a','https://1drv.com.evil.invalid/a','https://127.0.0.1/a','https://u:p@fixture.1drv.com/a','https://my.microsoftpersonalcontent.com.evil.invalid/a','https://mediap.svc.ms.evil.invalid/a','http://my.microsoftpersonalcontent.com/a','https://francecentral1-mediap.svc.ms:8080/a']:
            with self.assertRaises(CloudError):safe_download(url)
        self.assertEqual(safe_download('https://fixture.1drv.com/a'),'https://fixture.1drv.com/a')
        for url in ('https://my.microsoftpersonalcontent.com/a','https://francecentral1-mediap.svc.ms/a'):
            self.assertEqual(safe_download(url),url)
        client=OneDrive(Path(self.temp.name)/'auth')
        try:
            with self.assertRaises(CloudError):client.get('https://evil.invalid/?access_token=x')
            with self.assertRaises(CloudError):client.configure('bad')
            client.configure('12345678-1234-1234-1234-123456789abc','consumers')
            self.assertTrue(client.state()['configured'])
            self.assertNotIn('tokens',client.state())
        finally:client.close()
    def test_personal_download_annotation_and_thumbnail_hosts(self):
        client=OneDrive(Path(self.temp.name)/'downloads')
        paths=[]
        def metadata(path):
            paths.append(path)
            if '/thumbnails' in path:return {'value':[{'large':{'url':'https://francecentral1-mediap.svc.ms/fixture'}}]}
            # Matches the real personal-account response: selecting the annotation drops it.
            if '?' in path:return {'id':'photo'}
            return {'id':'photo','@microsoft.graph.downloadUrl':'https://my.microsoftpersonalcontent.com/fixture'}
        from unittest.mock import MagicMock
        response=MagicMock();response.__enter__.return_value.read.return_value=b'fixture-image'
        try:
            with patch.object(client,'get',side_effect=metadata),patch.object(client.binary,'open',return_value=response) as opened:
                self.assertEqual(client.content_url('drive','photo'),'https://my.microsoftpersonalcontent.com/fixture')
                self.assertEqual(client.image_bytes('drive','photo',True),b'fixture-image')
                self.assertEqual(client.image_bytes('drive','photo'),b'fixture-image')
                for call in opened.call_args_list:
                    self.assertFalse(call.args[0].has_header('Authorization'))
                self.assertTrue(all('$select' not in path for path in paths))
        finally:client.close()

    @unittest.skipUnless(os.name=='nt','Windows DPAPI')
    def test_tokens_encrypted_at_rest_and_not_in_status(self):
        client=OneDrive(Path(self.temp.name)/'vault')
        try:
            client._save_tokens({'access_token':'private-test-access','refresh_token':'private-test-refresh','expires_in':3600})
            data=(client.root/'tokens.bin').read_bytes()
            self.assertNotIn(b'private-test-access',data)
            self.assertEqual(json.loads(crypt(data,True))['refresh_token'],'private-test-refresh')
            self.assertNotIn('private-test',json.dumps(client.state()))
            client.disconnect();self.assertFalse((client.root/'tokens.bin').exists())
        finally:client.close()
