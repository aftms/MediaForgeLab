import copy
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from catalog import Catalog
from provider import Provider
from refresh import RefreshManager, atomic_batch, recover, normalize, merge, read_json


class FixtureProvider(Provider):
    def __init__(self):
        super().__init__('http://Fixture.invalid:8000/get.php?username=User%2BOne&password=Secret%2FCase')
        self.calls=[]
        self.fail=None
        self.empty=None
        self.episodes=[dict(id=31,title='Primeiro',season=1,episode_num=1,container_extension='mkv')]
    def fetch(self, action, **parameters):
        self.calls.append(action)
        if action==self.fail:
            raise OSError('fixture connection failed with private-secret')
        if action==self.empty:
            return []
        if action.endswith('_categories'):
            return [dict(category_id='1',category_name='PT| Geral'),dict(category_id='2',category_name='BR| Cinema')]
        if action=='get_series_info':
            return {'episodes':{'1':self.episodes},'seasons':[1],'info':{}}
        if action=='get_series':
            return [dict(series_id=20,name='Série renovada',category_id=1,cover='http://fixture.invalid/cover.jpg')]
        if action=='get_vod_streams':
            return [dict(stream_id=10,name='Filme atualizado',category_id=1,category_ids=[1,2],container_extension='mp4',stream_icon='http://fixture.invalid/new.jpg')]
        if action=='get_live_streams':
            return [dict(stream_id=100,name='Canal renomeado HD',category_id=1),dict(stream_id=101,name='Novo SD',category_id=1),dict(stream_id=101,name='Novo HD',category_id=1)]
        raise AssertionError('Not a metadata operation')


class RefreshTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.config=dict(favorites_path=str(self.root/'favorites.json'))
        self.provider=FixtureProvider()
        self.catalog=Catalog([dict(id=1,name='Canal antigo SD',group='PT| Geral',url=self.provider.media_url('live','100'))],self.config)
        self.catalog.add(dict(id='m10',provider_id='10',kind='movie',name='Filme antigo',group='PT| Geral',extension='mp4',url=self.provider.media_url('movie','10','mp4')))
        self.catalog.provider=self.provider
        self.server=SimpleNamespace(catalog=self.catalog,config=self.config,catalog_lock=threading.RLock())
        self.manager=RefreshManager(self.server,self.root/'runtime',self.root/'exports')
    def tearDown(self):
        self.temp.cleanup()
    def run_update(self):
        self.manager.start()
        self.manager.thread.join(5)
        self.assertFalse(self.manager.status()['running'])

    def test_watched_episode_is_restored_after_restart_without_provider_requests(self):
        self.run_update()
        episodes=self.server.catalog.episodes('s20')
        identifier=episodes[0]['id']
        self.server.catalog.by_id.pop(identifier)
        before=list(self.provider.calls)
        self.manager.restore_progress_episodes({identifier:{'position':45}})
        self.assertEqual(self.server.catalog.by_id[identifier]['kind'],'episode')
        self.assertEqual(self.provider.calls,before)
    def test_upsert_ids_metadata_favorites_and_order_without_streams(self):
        self.catalog.favorite('1',True)
        key=self.catalog.by_id['1']['key']
        self.run_update()
        self.assertFalse(self.manager.status()['error'])
        self.assertEqual(self.manager.status()['summary']['added'],dict(tv=1,movie=0,series=1))
        self.assertEqual(self.server.catalog.by_id['1']['name'],'Canal renomeado HD')
        self.assertEqual(self.server.catalog.by_id['1']['key'],key)
        self.assertTrue(self.server.catalog.public(self.server.catalog.by_id['1'])['favorite'])
        self.assertEqual(self.server.catalog.by_id['m10']['cover'],'http://fixture.invalid/new.jpg')
        self.assertEqual(self.server.catalog.browse(dict(kind='movie',group='BR| Cinema'))['total'],1)
        self.assertEqual([i['id'] for i in self.server.catalog.by_kind['tv']],['1','2'])
        self.assertTrue((self.root/'exports'/'canais-completos.m3u').read_text().startswith('#EXTM3U'))
        self.assertNotIn('get_series_info',self.provider.calls)
        self.server.catalog.provider=self.provider
        self.run_update()
        self.assertEqual(self.manager.status()['summary']['added'],dict(tv=0,movie=0,series=0))
        self.assertEqual(self.server.catalog.counts(),dict(tv=2,movie=1,series=1))
    def test_failed_and_empty_updates_preserve_files_favorites_and_last_success(self):
        self.run_update()
        original=self.server.catalog
        paths=list((self.root/'exports').rglob('*'))+[self.root/'runtime'/'catalog-current.json']
        contents={p:p.read_bytes() for p in paths if p.is_file()}
        last=self.manager.status()['last_success']
        for mode in ('fail','empty'):
            self.server.catalog.provider=self.provider
            setattr(self.provider,mode,'get_vod_streams')
            self.run_update()
            self.assertIs(self.server.catalog,original)
            self.assertEqual(self.manager.status()['last_success'],last)
            self.assertIn('preservado',self.manager.status()['error'])
            self.assertNotIn('private-secret',str(self.manager.status()))
            for path,value in contents.items(): self.assertEqual(path.read_bytes(),value)
            setattr(self.provider,mode,None)
    def test_missing_ids_are_retained_and_ids_are_typed(self):
        old=[dict(id='1',provider_id='10',kind='tv',name='TV',group='PT',country='PT'),dict(id='m10',provider_id='10',kind='movie',name='Filme',group='PT')]
        rows,summary=merge(old,dict(tv={},movie={},series={'10':dict(provider_id='10',kind='series',name='Série',group='PT')}))
        self.assertEqual([i['id'] for i in rows],['1','m10','s10'])
        self.assertEqual(summary['added']['series'],1)
    def test_lazy_new_seasons_and_episode_ids_and_fallback(self):
        self.run_update()
        cat=self.server.catalog;cat.provider=self.provider
        first=cat.episodes('s20')
        self.assertEqual(first[0]['id'],'e31')
        self.assertIn('/31.mkv',first[0]['url'])
        self.assertNotIn('/20.mkv',first[0]['url'])
        self.provider.episodes.append(dict(id=32,title='Nova temporada',season=2,episode_num=1,container_extension='mp4'))
        cat.series_checked.clear()
        self.assertEqual(len(cat.episodes('s20')),2)
        self.assertEqual(cat.episode_status['s20']['added'],1)
        self.assertEqual(cat.episodes('s20')[1]['season'],'2')
        playlist=self.root/'exports'/'series-episodios.m3u'
        previous=playlist.read_bytes()
        cat.series_checked.clear();self.provider.fail='get_series_info'
        self.assertEqual(len(cat.episodes('s20')),2)
        self.assertEqual(cat.episode_status['s20']['status'],'cached_after_error')
        seasons=cat.browse(dict(view='seasons',series='s20'))
        self.assertEqual(sum(row['count'] for row in seasons['items']),2)
        self.assertEqual(seasons['episodes']['status'],'cached_after_error')
        self.assertEqual(playlist.read_bytes(),previous)
    def test_one_background_job_and_favorite_changed_during_download(self):
        gate=threading.Event();entered=threading.Event();fetch=self.provider.fetch
        def slow(action,**kwargs):
            if action=='get_live_categories':entered.set();gate.wait(3)
            return fetch(action,**kwargs)
        self.provider.fetch=slow
        self.manager.start();self.assertTrue(entered.wait(1));thread=self.manager.thread
        self.manager.start();self.assertIs(self.manager.thread,thread)
        self.server.catalog.favorite('1',True)
        gate.set();thread.join(5)
        self.assertTrue(self.server.catalog.public(self.server.catalog.by_id['1'])['favorite'])
    def test_source_private_and_active_source_only_changes_after_success(self):
        active=self.server.catalog.provider
        info=self.manager.set_source('http://Other.invalid:9000/get.php?username=User%2B&password=Secret%26Case')
        self.assertEqual(info,dict(configured=True,server='http://Other.invalid:9000'))
        self.assertIs(self.server.catalog.provider,active)
        self.assertNotIn('Secret',str(info))
        self.assertEqual(self.manager.source().password,'Secret&Case')
        with self.assertRaises(ValueError):self.manager.set_source('http://bad.invalid/get.php?username=a')

    def test_restart_restores_snapshot_favorites_progress_and_update_time(self):
        import ipaddress
        from server import PortalServer
        self.catalog.favorite('1',True)
        self.run_update()
        runtime=self.root/'runtime'
        (runtime/'progress.json').write_text(json.dumps({'m10':{'position':120,'completed':False}}))
        config=dict(self.config,host='127.0.0.1',port=0,network=ipaddress.ip_network('127.0.0.0/24'),
                    provider_metadata=True,runtime_path=str(runtime),export_dir=str(self.root/'exports'))
        restored=PortalServer(config,[],{},'fixture-control')
        try:
            self.assertEqual(restored.catalog.counts(),dict(tv=2,movie=1,series=1))
            self.assertTrue(restored.catalog.public(restored.catalog.by_id['1'])['favorite'])
            self.assertEqual(restored.progress['m10']['position'],120)
            self.assertEqual(restored.updater.status()['last_success'],self.manager.status()['last_success'])
        finally:
            restored.server_close()


class TransactionTests(unittest.TestCase):
    def test_mid_commit_failure_rolls_back_all_targets(self):
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);a=root/'a.json';b=root/'b.json';a.write_text('old')
            import os
            def fail_second(source,target):
                if Path(target)==b:raise OSError('disk failure')
                os.replace(source,target)
            with self.assertRaises(OSError):atomic_batch({a:b'new',b:b'other'},root/'journal.json',replace=fail_second)
            self.assertEqual(a.read_text(),'old');self.assertFalse(b.exists())
            self.assertEqual(sorted(p.name for p in root.iterdir()),['a.json'])
    def test_crash_recovery_and_validation_before_replace(self):
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);a=root/'a.json';backup=root/'a.bak';journal=root/'journal.json'
            a.write_text('partial');backup.write_text('original')
            journal.write_text(json.dumps([dict(target=str(a),backup=str(backup),temp=str(root/'temp'),existed=True)]))
            recover(journal);self.assertEqual(a.read_text(),'original')
            def bad(*args):raise ValueError('invalid content')
            with self.assertRaises(ValueError):atomic_batch({a:b'bad'},journal,validator=bad)
            self.assertEqual(a.read_text(),'original')
    def test_url_parser_preserves_credentials_case_port_and_encoding(self):
        p=Provider('http://Fixture.invalid:8000/get.php?username=MiX%2BName&password=P%26%2F%3F')
        self.assertEqual(p.origin,'http://Fixture.invalid:8000')
        self.assertEqual(p.user,'MiX+Name');self.assertEqual(p.password,'P&/?')
        media=p.media_url('live','123')
        restored=Provider(media)
        self.assertEqual((restored.user,restored.password),(p.user,p.password))
        self.assertEqual(Provider(p.source_url()).password,p.password)


if __name__=='__main__':unittest.main()
