import json
import http.client
import ipaddress
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from catalog import Catalog
from favorite_layout import FavoriteLayout, LayoutError
from server import PortalServer


class FavoriteLayoutTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.config={'favorites_path':str(self.root/'favorites.json')}
        self.rows=[dict(id=str(i),name=name,group='PT| Geral',url='http://fixture.invalid/'+str(i)+'.ts')
                   for i,name in enumerate(('Alfa HD','Beta HD','Gama HD','Alfa FHD'),1)]
        self.catalog=Catalog(self.rows,self.config)
        for kind in ('movie','series'):
            self.catalog.add(dict(id=kind+'1',kind=kind,name='Título',group='PT'))
        for identifier in ('1','2','3','movie1','series1'):self.catalog.favorite(identifier,True)
        self.layout=FavoriteLayout(self.root/'layout.json')

    def tearDown(self):self.temp.cleanup()

    def update(self,operation,kind='tv',**kw):
        return self.layout.update(self.catalog,dict(operation=operation,kind=kind,revision=self.layout.read()['revision'],**kw))

    def browse(self,**kw):return self.layout.browse(self.catalog,dict(kind='tv',**kw))

    def test_folder_crud_never_removes_favorites_and_is_typed(self):
        favorites=self.catalog.favorites.copy()
        original=(self.root/'favorites.json').read_bytes()
        folder=self.update('create',name='Desporto')['folder']
        self.update('assign',id='1',folder=folder)
        self.assertEqual([i['id'] for i in self.browse(folder=folder)['items']],['4'])
        self.assertEqual(self.browse()['ungrouped_count'],2)
        self.assertEqual(self.layout.browse(self.catalog,{'kind':'movie'})['folders'],[])
        with self.assertRaises(LayoutError):self.update('assign',kind='movie',id='movie1',folder=folder)
        self.update('rename',folder=folder,name='Televisão')
        self.assertEqual(self.browse()['folders'][0]['name'],'Televisão')
        self.update('delete',folder=folder)
        self.assertEqual(self.browse(folder='ungrouped')['total'],3)
        self.assertEqual(self.catalog.favorites,favorites)
        self.assertEqual((self.root/'favorites.json').read_bytes(),original)

    def test_order_quality_filter_restart_and_readded_favorites(self):
        self.update('move',id='3',direction='first')
        self.assertEqual([i['id'] for i in self.browse()['items']],['3','4','2'])
        self.assertEqual([i['id'] for i in self.browse(quality='HD')['items']],['3','1','2'])
        self.assertEqual(self.browse(offset='1',limit='1')['items'][0]['id'],'4')
        self.layout=FavoriteLayout(self.root/'layout.json')
        self.catalog=Catalog(self.rows,self.config)
        self.assertEqual(self.browse()['items'][0]['id'],'3')
        self.catalog.favorite('3',False)
        self.assertEqual(self.browse()['total'],2)
        self.catalog.favorite('3',True)
        self.assertEqual(self.browse()['items'][0]['id'],'3')

    def test_reorder_one_folder_preserves_other_slots_and_conflict(self):
        folder=self.update('create',name='Seleção')['folder']
        self.update('assign',id='1',folder=folder)
        self.update('assign',id='3',folder=folder)
        revision=self.layout.read()['revision']
        self.update('move',id='3',folder=folder,direction='first')
        self.assertEqual([i['id'] for i in self.browse()['items']],['3','2','4'])
        with self.assertRaises(LayoutError) as error:
            self.layout.update(self.catalog,dict(kind='tv',operation='rename',folder=folder,name='Outro',revision=revision))
        self.assertEqual(error.exception.status,409)
        self.assertEqual(self.browse()['folders'][0]['name'],'Seleção')

    def test_empty_duplicate_and_unknown_inputs_are_rejected(self):
        self.update('create',name='Cinema',kind='movie')
        for name in ('', 'x'*61, 'CINEMA'):
            with self.assertRaises(LayoutError):self.update('create',kind='movie',name=name)
        self.update('create',name='Cinema',kind='series')
        with self.assertRaises(LayoutError):self.update('assign',id='missing')
        with self.assertRaises(LayoutError):self.update('move',id='1',direction='unknown')

    def test_corruption_and_failed_save_preserve_existing_data(self):
        self.update('create',name='Pasta')
        original=self.layout.path.read_bytes()
        with patch('favorite_layout.atomic_batch',side_effect=OSError('disk full')):
            with self.assertRaises(OSError):self.update('create',name='Nova')
        self.assertEqual(self.layout.path.read_bytes(),original)
        self.layout.path.write_bytes(b'{broken')
        with self.assertRaises(OSError):self.update('create',name='Nova')
        self.assertEqual(self.layout.path.read_bytes(),b'{broken')
        self.layout.path.write_text(json.dumps({'schema':1,'revision':1,'folders':[],'placements':{},'order':{}}))
        with self.assertRaises(OSError):self.browse()

    def test_http_requires_action_token_and_reports_revision_conflicts(self):
        cfg=dict(host='127.0.0.1',port=0,network=ipaddress.ip_network('127.0.0.0/24'),runtime_path=str(self.root/'http'),switch_delay_ms=1000,player_solution='ffmpeg')
        app=PortalServer(cfg,self.rows,{},'fixture')
        thread=threading.Thread(target=app.serve_forever,kwargs={'poll_interval':.02},daemon=True)
        thread.start()
        def post(headers):
            connection=http.client.HTTPConnection(*app.server_address,timeout=3)
            connection.request('POST','/api/favorites/layout',headers=headers,body=json.dumps(dict(operation='create',kind='tv',name='Pasta',revision=0)))
            response=connection.getresponse();body=json.loads(response.read());connection.close()
            return response.status,body
        try:
            self.assertEqual(post({})[0],403)
            self.assertEqual(post({'X-MAG-Action':app.action_token,'Origin':'https://foreign.invalid'})[0],403)
            self.assertFalse(app.favorite_layout.path.exists())
            self.assertEqual(post({'X-MAG-Action':app.action_token})[0],200)
            self.assertEqual(post({'X-MAG-Action':app.action_token})[0],409)
            self.assertEqual(len(app.favorite_layout.read()['folders']),1)
        finally:
            app.shutdown();app.server_close();thread.join(2)

    def test_large_favorite_pages_and_move_across_page_boundary(self):
        for i in range(300):
            item=self.catalog.add(dict(id='m'+str(i),kind='movie',name='Filme %03d'%i,group='PT'))
            self.catalog.favorites.add(item['key'])
        self.catalog.cache.clear()
        data=self.layout.browse(self.catalog,dict(kind='movie',limit='240'))
        self.assertEqual(len(data['items']),240)
        self.assertEqual(data['total'],301)
        self.update('move',kind='movie',id='m0',direction='last')
        last=self.layout.browse(self.catalog,dict(kind='movie',limit='60',offset='300'))
        self.assertEqual([i['id'] for i in last['items']],['m0'])
        self.assertEqual(last['items'][0]['favorite_position'],301)


if __name__=='__main__':unittest.main()
