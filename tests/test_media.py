import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from media import MediaManager, MediaError
from catalog import Catalog


class MediaTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        catalog=Catalog([dict(id='1',name='Canal',group='PT',url='http://fixture.invalid/live/private/secret/1.ts')],{})
        catalog.add(dict(id='m2',kind='movie',name='Filme',group='PT',url='http://fixture.invalid/movie/private/secret/2.mp4'))
        self.app=SimpleNamespace(runtime=Path(self.temp.name),config={'ffmpeg':'fixture','ffprobe':'fixture','loopback_port':1},catalog=catalog,progress={'m2':{'position':120,'duration':1000}})
        self.media=MediaManager(self.app)
        self.prepare=patch.object(self.media,'_prepare',lambda session:None)
        self.prepare.start()

    def tearDown(self):
        self.media.close()
        self.prepare.stop()
        self.temp.cleanup()

    def test_web_and_mag_exclude_each_other_and_hide_provider(self):
        web=self.media.start({'id':'m2','owner':'browser-owner-1'},'192.168.1.5','web')
        self.assertEqual(web['position'],120)
        self.assertNotIn('secret',json.dumps(web))
        self.assertNotIn('url',web)
        with self.assertRaises(MediaError):
            self.media.start({'id':'1','owner':'mag-device-owner'},'192.168.1.6','mag')
        self.assertEqual(self.media.status()['device'],'Navegador')
        with self.assertRaises(MediaError):
            self.media.release({'token':web['token']},'192.168.1.6')
        self.media.release({'token':web['token']},'192.168.1.5')
        mag=self.media.start({'id':'1','owner':'mag-device-owner'},'192.168.1.6','mag')
        with self.assertRaises(MediaError):
            self.media.start({'id':'m2','owner':'browser-owner-1'},'192.168.1.5','web')
        self.assertEqual(self.media.pulse({'token':mag['token']},'192.168.1.6')['state'],'ready')

    def test_concurrent_devices_only_one_wins(self):
        barrier=threading.Barrier(2)
        results=[]
        def start(number):
            barrier.wait()
            try:
                self.media.start({'id':'1','owner':'fixture-owner-'+str(number)},'192.168.1.'+str(number),'mag')
                results.append('started')
            except MediaError:
                results.append('blocked')
        threads=[threading.Thread(target=start,args=(i,)) for i in (5,6)]
        for thread in threads:thread.start()
        for thread in threads:thread.join()
        self.assertCountEqual(results,['started','blocked'])

    def test_samsung_android_and_browser_share_the_same_lease(self):
        samsung=self.media.start({'id':'m2','owner':'samsung-owner-1','device':'samsung'},'192.168.1.9','web')
        self.assertEqual(self.media.status()['device'],'Samsung TV')
        with self.assertRaises(MediaError):
            self.media.start({'id':'m2','owner':'android-owner-2','device':'androidtv'},'192.168.1.10','web')
        with self.assertRaises(MediaError):
            self.media.start({'id':'m2','owner':'browser-owner-3'},'192.168.1.9','web')
        self.media.release({'token':samsung['token']},'192.168.1.9')
        self.media.start({'id':'m2','owner':'android-owner-2','device':'androidtv'},'192.168.1.10','web')
        self.assertEqual(self.media.status()['device'],'Android TV')


    def test_same_owner_switch_invalidates_old_token_and_no_path_traversal(self):
        old=self.media.start({'id':'1','owner':'fixture-owner-1'},'192.168.1.5','web')
        new=self.media.start({'id':'m2','owner':'fixture-owner-1','position':30},'192.168.1.5','web')
        self.assertNotEqual(old['token'],new['token'])
        with self.assertRaises(MediaError):self.media.pulse({'token':old['token']},'192.168.1.5')
        with self.assertRaises(MediaError):self.media.segment(new['token'],'../../source.json','192.168.1.5')
        self.media.release({'owner':'fixture-owner-1'},'192.168.1.5')
        self.assertFalse(self.media.status()['active'])

    def test_invalid_owner_or_item_never_opens_provider(self):
        for data in ({'owner':'x','id':'1'},{'owner':'fixture-owner-1','id':'s123'},{'owner':'fixture-owner-1','id':'m2','position':-1}):
            with self.assertRaises(MediaError):self.media.start(data,'192.168.1.5','web')
        self.assertFalse(self.media.status()['active'])

    def test_invalid_seek_preserves_current_session_and_internal_reads_do_not_renew(self):
        session=self.media.start({'id':'m2','owner':'fixture-owner-1'},'192.168.1.5','web')
        for position in (-1, 'bad', float('nan'), float('inf')):
            with self.assertRaises(MediaError):
                self.media.start({'id':'m2','owner':'fixture-owner-1','position':position},'192.168.1.5','web')
        self.assertEqual(self.media.session['token'],session['token'])
        self.media.session['seen']=1
        self.media._get(session['token'],touch=False)
        self.assertEqual(self.media.session['seen'],1)
        self.media.pulse({'token':session['token']},'192.168.1.5')
        self.assertGreater(self.media.session['seen'],1)

    def test_delayed_mag_start_and_stop_cannot_resurrect_or_stop_new_channel(self):
        owner='fixture-mag-owner'
        ip='192.168.1.5'
        self.media.release({'owner':owner,'request_id':1},ip)
        with self.assertRaises(MediaError):
            self.media.start({'owner':owner,'id':'1','request_id':1},ip,'mag')
        current=self.media.start({'owner':owner,'id':'1','request_id':2},ip,'mag')
        self.media.release({'owner':owner,'request_id':1},ip)
        self.assertEqual(self.media.session['token'],current['token'])
        self.media.release({'owner':owner,'request_id':2},ip)
        self.assertFalse(self.media.status()['active'])


if __name__=='__main__':
    unittest.main()
