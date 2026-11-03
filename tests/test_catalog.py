import base64
import json
import os
from unittest.mock import patch
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from catalog import Catalog, quality, country_for, family_key
from provider import Provider, decode_epg


def tv(identifier, name, group='PT| GENERALISTAS'):
    return {'id':identifier, 'name':name, 'group':group, 'url':'http://fixture.invalid/live/private-user/private-secret/%s.ts' % identifier}


class FakeProvider:
    def __init__(self):
        self.calls = []

    def fetch(self, action, **parameters):
        self.calls.append((action, parameters))
        if action == 'get_series_info':
            return {'episodes': {'2':[{'id':'202', 'episode_num':1, 'title':'Regresso', 'container_extension':'mkv'}],
                                 '1':[{'id':'201', 'episode_num':1, 'title':'Início', 'container_extension':'mp4'}]}}
        return {'epg_listings':[{'title':base64.b64encode('Notícias'.encode()).decode(), 'description':base64.b64encode('Programa real'.encode()).decode(),
                                'start':'2026-11-02 18:00:00','end':'2026-11-02 19:00:00'}]}

    def media_url(self, kind, identifier, extension):
        return 'http://fixture.invalid/%s/%s.%s' % (kind,identifier,extension)


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.config = {'favorites_path':str(Path(self.temp.name)/'favorites.json')}
        self.rows = [tv(1,'MEO: RTP 1 SD'),tv(2,'RTP 1 HD'),tv(3,'RTP 1 FHD'),tv(4,'RTP 1 4K'),
                     tv(5,'Câmara TV HD'),tv(6,'Canal desconhecido'),tv(7,'Canal España HD','ES| GENERAL'),tv(8,'RTP 2 HD')]
        self.catalog = Catalog(self.rows, self.config)

    def tearDown(self):
        self.temp.cleanup()

    def test_auto_and_explicit_quality_remove_variants(self):
        result = self.catalog.browse(dict(kind='tv',country='PT',q='RTP 1',quality='auto'))
        self.assertEqual([i['id'] for i in result['items']], ['3'])
        self.assertEqual(self.catalog.browse(dict(kind='tv',q='RTP 1',quality='HD'))['items'][0]['id'], '2')
        self.assertEqual(self.catalog.browse(dict(kind='tv',q='RTP 1',quality='all'))['total'], 4)
        self.assertEqual(quality('CANAL Full HD'),'FHD')
        self.assertEqual(quality('Canal sem indicação'),'UNKNOWN')
        self.assertEqual(family_key(dict(kind='tv',name='VO: RTP 1 HD',country='PT')),family_key(dict(kind='tv',name='VIP: RTP 1 SD',country='PT')))

    def test_large_web_pages_are_complete_without_changing_mag_limits(self):
        for i in range(301):
            self.catalog.add(dict(id='m'+str(i),kind='movie',name='Filme '+str(i),group='PT'))
        first=self.catalog.browse(dict(kind='movie',client='web',limit='120'))
        second=self.catalog.browse(dict(kind='movie',client='web',limit='120',offset='120'))
        self.assertEqual(len(first['items']),120)
        self.assertEqual(len(second['items']),120)
        self.assertFalse({i['id'] for i in first['items']} & {i['id'] for i in second['items']})
        self.assertEqual(len(self.catalog.browse(dict(kind='movie',client='web',limit='9999'))['items']),240)
        self.assertEqual(len(self.catalog.browse(dict(kind='movie',limit='9999'))['items']),30)
        self.assertEqual(len(self.catalog.browse(dict(kind='movie'))['items']),10)

    def test_countries_regions_and_accent_insensitive_search(self):
        self.assertEqual(self.catalog.browse(dict(view='countries'))['items'][0]['name'], 'Portugal')
        self.assertEqual(self.catalog.browse(dict(kind='tv',q='camara'))['items'][0]['name'],'Câmara TV HD')
        self.assertEqual(country_for('AR| ARGENTINA'),'AR')
        self.assertEqual(country_for('AR| SHAHID VIP'),'ARAB')
        self.assertEqual(country_for('HR| HORSE RACING'),'OTHER')

    def test_favorites_persist_by_channel_family_and_work_after_quality_change(self):
        self.catalog.favorite('2', True)
        restored = Catalog(self.rows,self.config)
        items = restored.browse(dict(kind='all',favorites='1',quality='auto'))['items']
        self.assertEqual([i['id'] for i in items],['3'])
        self.assertTrue(items[0]['favorite'])
        restored.favorite('3',False)
        self.assertEqual(restored.browse(dict(kind='all',favorites='1'))['total'],0)
        raw = Path(self.config['favorites_path']).read_text()
        self.assertNotIn('private-secret',raw)
        self.assertNotIn('fixture.invalid',raw)

    def test_favorites_backup_history_noop_and_failed_write(self):
        path = Path(self.config['favorites_path'])
        history = path.with_suffix('.history.json')
        backup = path.with_suffix('.backup.json')
        self.catalog.favorite('2', True)
        self.assertEqual(json.loads(backup.read_text()), [])
        self.assertEqual(len(json.loads(history.read_text())), 1)
        before = {p: p.read_bytes() for p in (path, history, backup)}
        self.catalog.favorite('3', True)  # Same family: no duplicate history or backup.
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        from storage import atomic_batch
        def fail_history(source, target):
            if Path(target) == history:
                raise OSError('Injected disk error')
            os.replace(source, target)
        with patch('catalog.atomic_batch', side_effect=lambda files, journal: atomic_batch(files, journal, replace=fail_history)):
            with self.assertRaises(OSError):
                self.catalog.favorite('2', False)
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        self.assertTrue(self.catalog.public(self.catalog.by_id['2'])['favorite'])
        self.catalog.favorite('2', False)
        self.assertEqual(json.loads(backup.read_text()), json.loads(before[path]))
        self.assertEqual([e['enabled'] for e in json.loads(history.read_text())], [True, False])
        self.assertEqual(Catalog(self.rows, self.config).favorites, set())
        self.assertNotIn('private-secret', history.read_text())

    def test_interrupted_favorite_write_recovers_before_loading(self):
        path = Path(self.config['favorites_path'])
        self.catalog.favorite('2', True)
        expected = set(self.catalog.favorites)
        backup, temp = path.with_suffix('.interrupted.bak'), path.with_suffix('.interrupted.tmp')
        backup.write_bytes(path.read_bytes())
        path.write_text('[]')  # Crash after one file was replaced, before transaction committed.
        journal = path.with_suffix('.journal.json')
        journal.write_text(json.dumps([dict(target=str(path), backup=str(backup), temp=str(temp), existed=True)]))
        self.assertEqual(Catalog(self.rows, self.config).favorites, expected)
        self.assertFalse(journal.exists())
        self.assertFalse(backup.exists())

    def test_invalid_favorites_are_never_silently_replaced(self):
        path = Path(self.config['favorites_path'])
        self.catalog.favorite('2', True)
        for invalid in ('[truncated', '{}', '[123]', '"wrong"'):
            path.write_text(invalid)
            with self.assertRaises(OSError):
                Catalog(self.rows, self.config)
            with self.assertRaises(OSError):
                self.catalog.favorite('2', False)
            self.assertEqual(path.read_text(), invalid)
        path.write_text('[]')
        with self.assertRaises(OSError):
            self.catalog.favorite('8', True)
        self.assertEqual(path.read_text(), '[]')

    def test_pagination_bounds_empty_and_safe_metadata(self):
        page=self.catalog.browse(dict(kind='tv',quality='all',limit='2',offset='4'))
        self.assertEqual(len(page['items']),2)
        self.assertEqual(page['offset'],4)
        self.assertNotIn('url',page['items'][0])
        self.assertEqual(self.catalog.browse(dict(kind='movie'))['total'],0)

    def test_series_is_browsed_before_play_and_episodes_are_ordered_and_cached(self):
        self.catalog.add(dict(id='s20',provider_id='20',name='Uma série',kind='series',group='PT'))
        provider=FakeProvider();self.catalog.provider=provider
        with self.assertRaises(ValueError):self.catalog.play_url('s20')
        result=self.catalog.browse(dict(view='episodes',series='s20'))
        self.assertEqual([i['id'] for i in result['items']],['e201','e202'])
        self.assertEqual(self.catalog.play_url('e202'),'http://fixture.invalid/series/202.mkv')
        self.catalog.episodes('s20');self.assertEqual(len(provider.calls),1)
        self.catalog.favorite('e201',True)
        self.assertEqual(self.catalog.browse(dict(kind='all',favorites='1'))['items'][0]['id'],'s20')

    def test_season_directories_filter_sort_and_page_without_new_provider_calls(self):
        self.catalog.add(dict(id='s20', provider_id='20', name='Uma série', kind='series', group='PT'))
        provider = FakeProvider()
        self.catalog.provider = provider
        data = {'episodes': {'10':[dict(id='1001', season=10, episode_num=1)],
            '2':[dict(id='210', season=2, episode_num=10), dict(id='202', season=2, episode_num=2)],
            '01':[dict(id='101', episode_num=1)], '0':[dict(id='1', episode_num=1)],
            '':[dict(id='999', episode_num=1)]}}
        with patch.object(provider, 'fetch', return_value=data) as fetch:
            result = self.catalog.browse(dict(view='seasons', series='s20'))
            self.assertEqual([r['name'] for r in result['items']],
                ['Especiais', 'Temporada 1', 'Temporada 2', 'Temporada 10', 'Sem temporada indicada'])
            self.assertEqual([r['count'] for r in result['items']], [1, 1, 2, 1, 1])
            self.assertTrue(all(r['kind']=='season' and 'url' not in r for r in result['items']))
            self.catalog.favorite('s20', True)
            self.assertTrue(all(r['favorite'] for r in self.catalog.browse(dict(view='seasons', series='s20'))['items']))
            page = self.catalog.browse(dict(view='episodes', series='s20', season='2', limit='1', offset='1'))
            self.assertEqual(page['total'], 2)
            self.assertEqual(page['items'][0]['id'], 'e210')
            self.assertEqual(self.catalog.browse(dict(view='episodes',series='s20',season='1'))['items'][0]['id'], 'e101')
            self.assertEqual(self.catalog.browse(dict(view='episodes',series='s20',season='unknown'))['total'], 1)
            self.assertEqual(self.catalog.browse(dict(view='episodes',series='s20',season='3'))['total'], 0)
            self.assertEqual(self.catalog.browse(dict(view='episodes',series='s20'))['total'], 6)  # Old clients.
            self.assertEqual(fetch.call_count, 1)
            self.assertEqual(fetch.call_args.args, ('get_series_info',))
        self.assertEqual(self.catalog.browse(dict(view='seasons',series='missing'))['total'], 0)

    def test_movie_and_series_favorites_survive_restart_and_episode_removal(self):
        media = [dict(id='m10',name='Um filme',kind='movie',group='PT'),
                 dict(id='s20',provider_id='20',name='Uma série',kind='series',group='PT')]
        for item in media:
            self.catalog.add(item)
        self.catalog.favorite('m10',True)
        self.catalog.favorite('s20',True)
        restored = Catalog(self.rows,dict(self.config,_playlist_media=media))
        restored.provider = FakeProvider()
        self.assertEqual({i['id'] for i in restored.browse(dict(kind='all',favorites='1'))['items']}, {'m10','s20'})
        self.assertTrue(all(i['favorite'] for i in restored.browse(dict(view='episodes',series='s20'))['items']))
        restored.favorite('e201',False)
        self.assertEqual([i['id'] for i in restored.browse(dict(kind='all',favorites='1'))['items']], ['m10'])
        self.assertFalse(any(i['favorite'] for i in restored.browse(dict(view='episodes',series='s20'))['items']))

    def test_epg_is_real_decoded_cached_and_not_a_media_request(self):
        self.catalog.provider=FakeProvider()
        result=self.catalog.epg('1')
        self.assertEqual(result['programs'][0]['title'],'Notícias')
        self.catalog.epg('1');self.assertEqual(len(self.catalog.provider.calls),1)
        self.assertEqual(self.catalog.provider.calls[0][0],'get_short_epg')
        self.assertEqual(decode_epg('Texto normal'),'Texto normal')

    def test_epg_uses_a_mapped_quality_variant_and_shares_the_family_cache(self):
        self.catalog.by_id['3']['epg_id']='station.test'
        self.catalog.provider=FakeProvider()
        self.assertEqual(self.catalog.epg('2')['status'],'ok')
        self.assertEqual(self.catalog.provider.calls[0][1]['stream_id'],'3')
        self.catalog.epg('1')
        self.assertEqual(len(self.catalog.provider.calls),1)

    def test_provider_rejects_arbitrary_actions_and_player_options(self):
        provider=Provider('http://fixture.invalid/live/private-user/private-secret/1.ts')
        with self.assertRaises(ValueError):provider.fetch('arbitrary_mutation')
        with self.assertRaises(ValueError):provider.fetch('get_series_info',series_id='../secret')
        with self.assertRaises(ValueError):provider.media_url('movie','3','mp4 atrack:2')

    def test_country_category_and_favorites_do_not_scan_the_whole_library(self):
        self.catalog.add(dict(id='m1',name='Filme PT',kind='movie',group='PT'))
        self.catalog.add(dict(id='m2',name='Filme ES',kind='movie',group='ES'))
        self.catalog.favorite('3',True)
        class NoScan(list):
            def __iter__(self):
                raise AssertionError('Global catalog scanned')
        self.catalog.items = NoScan(self.catalog.items)
        self.assertEqual(self.catalog.counts()['movie'],2)
        self.assertEqual(self.catalog.browse(dict(kind='movie',group='PT'))['total'],1)
        self.assertEqual(self.catalog.browse(dict(kind='tv',country='ES'))['total'],1)
        self.assertEqual(self.catalog.browse(dict(kind='all',favorites='1'))['total'],1)
        self.assertEqual(self.catalog.browse(dict(kind='movie',view='groups'))['total'],3)
        self.assertEqual(self.catalog.browse(dict(kind='tv',view='countries'))['total'],2)

    def test_directory_pages_reuse_summary_and_invalidate_on_new_item(self):
        params=dict(kind='tv',view='countries',limit='1')
        self.catalog.browse(params)
        original = self.catalog.selection
        self.catalog.selection = lambda _: self.fail('Directory recomputed for next page')
        self.assertEqual(self.catalog.browse(dict(params,offset='1'))['offset'],1)
        self.catalog.selection = original
        self.catalog.add(dict(tv(50,'Canal FR','FR| TV'),kind='tv',country='FR'))
        self.assertEqual(self.catalog.browse(params)['total'],3)


if __name__ == '__main__':
    unittest.main()
