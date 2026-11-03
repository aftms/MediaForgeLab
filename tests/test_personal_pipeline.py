import json
from pathlib import Path
import shutil
import subprocess
import time
import unittest
import urllib.request
import urllib.error
from media import MediaError,process_options
from personal_fixture import Fixture

@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg required')
class PersonalPipelineTests(unittest.TestCase):
    def test_cloud_pipeline_seek_cleanup_and_independent_provider_lease(self):
        f=Fixture()
        try:
            # Real HTTP routes enforce the same LAN/origin/CSRF boundaries.
            body=json.dumps({'operation':'favorite','id':f.photo,'favorite':True}).encode()
            request=urllib.request.Request(f.url+'/api/personal',body,{'Content-Type':'application/json'})
            with self.assertRaises(urllib.error.HTTPError) as failure:urllib.request.urlopen(request)
            self.assertEqual(failure.exception.code,403);failure.exception.close()
            request.add_header('X-MAG-Action',f.app.action_token)
            with urllib.request.urlopen(request) as response:self.assertTrue(json.load(response)['saved'])
            request.add_header('Origin','https://outside.invalid')
            with self.assertRaises(urllib.error.HTTPError) as failure:urllib.request.urlopen(request)
            self.assertEqual(failure.exception.code,403);failure.exception.close()
            for path in ('/.runtime/personal/tokens.bin','/personal/raw/invalid','/personal/image/invalid'):
                with self.assertRaises(urllib.error.HTTPError) as failure:urllib.request.urlopen(f.url+path)
                self.assertIn(failure.exception.code,(400,403,404,409,410));failure.exception.close()
            supplier=f.app.media.start({'id':'fixture-vod','owner':'fixture-provider-owner'},'127.0.0.1','web')
            personal=f.app.personal_media.start({'id':f.video,'owner':'fixture-personal-owner','position':3},'127.0.0.1','web')
            for manager in (f.app.media,f.app.personal_media):
                deadline=time.monotonic()+35
                while time.monotonic()<deadline and manager.status()['active'] and manager.status()['state']!='ready':time.sleep(.1)
                self.assertEqual(manager.status()['state'],'ready',manager.status())
            with self.assertRaises(MediaError):f.app.personal_media.start({'id':f.video,'owner':'another-personal-owner'},'127.0.0.2','web')
            ready=f.app.personal_media.pulse(personal,'127.0.0.1');self.assertEqual(ready['position'],3);self.assertEqual(ready['video_mode'],'remux')
            with urllib.request.urlopen(f.url+ready['url']) as r:self.assertIn(b'#EXTM3U',r.read())
            folder=f.app.personal_media.root/personal['token'];segment=next(folder.glob('s*.ts'))
            result=subprocess.run([shutil.which('ffprobe'),'-v','quiet','-show_streams','-of','json',str(segment)],stdout=subprocess.PIPE,check=True,**process_options())
            streams=json.loads(result.stdout)['streams'];self.assertTrue(any(s['codec_type']=='video' and s['codec_name']=='h264' for s in streams))
            f.app.personal_media.release(personal,'127.0.0.1');self.assertFalse(folder.exists());self.assertTrue(f.app.media.status()['active'])
            again=f.app.personal_media.start({'id':f.video,'owner':'fixture-personal-owner','position':8,'compatibility':True},'127.0.0.1','web')
            deadline=time.monotonic()+35
            while time.monotonic()<deadline and f.app.personal_media.status()['active'] and f.app.personal_media.status()['state']!='ready':time.sleep(.1)
            self.assertEqual(f.app.personal_media.pulse(again,'127.0.0.1')['video_mode'],'transcode')
            f.app.personal_media.release(again,'127.0.0.1');f.app.media.release(supplier,'127.0.0.1')
        finally:f.close()
