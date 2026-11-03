import ipaddress
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
import time
from unittest.mock import patch
import urllib.request
import urllib.error
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from collections_store import Collections, CollectionError, source_url
from server import PortalServer

YT='https://www.youtube.com/watch?v=M7lc1UVf-VE'
class StoreTests(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory();self.store=Collections(self.temp.name)
 def tearDown(self):self.store.close();self.temp.cleanup()
 def put(self,op,**data):return self.store.update(dict(operation=op,**data))
 def item(self,url=YT,**data):return self.put('item-save',url=url,**data)['id']
 def test_dedup_preserves_favorite_progress_metadata(self):
  id=self.item(title='Original');self.put('favorite',id=id,favorite=True);self.put('progress',id=id,position=31,duration=180)
  for url in ('https://youtu.be/M7lc1UVf-VE?t=4','https://youtube.com/shorts/M7lc1UVf-VE','https://www.youtube.com/embed/M7lc1UVf-VE'):
   self.assertEqual(self.item(url),id)
  row=self.store.get(id);self.assertEqual(row['title'],'Original');self.assertEqual(row['position'],31);self.assertTrue(row['favorite']);self.assertEqual(self.store.browse({})['total'],1)
 def test_category_tree_search_move_cycle_delete(self):
  root=self.put('category-save',name='Culinária')['id'];child=self.put('category-save',name='Vegetariano',parent=root)['id'];id=self.item(categories=[child],title='Receita')
  self.assertEqual(self.store.browse({'category':root})['total'],1)
  with self.assertRaises(CollectionError):self.put('category-save',id=root,name='Ciclo',parent=child)
  with self.assertRaises(CollectionError):self.put('category-delete',id=root)
  self.assertEqual(self.store.browse({'q':'receita'})['total'],1)
  self.put('category-delete',id=child);self.put('category-delete',id=root);self.assertEqual(self.store.get(id)['categories'],[])
 def test_import_is_atomic_and_deduplicated(self):
  with self.assertRaises(CollectionError):self.put('import',items=[YT,'javascript:alert(1)'])
  self.assertEqual(self.store.browse({})['total'],0)
  result=self.put('import',items=[{'source_url':YT,'name':'Demo'},YT]);self.assertEqual((result['added'],result['existing']),(1,1))
 def test_playlist_order_repeated_entries_progress_and_persistence(self):
  a=self.item();b=self.item('https://vimeo.com/76979871');p=self.put('playlist-save',name='Treino')['id']
  for id in (a,b,a):self.put('playlist-add',id=id,playlist=p)
  queue=self.store.browse({'operation':'queue','playlist':p})['items'];entry=queue[2]['entry_id'];self.put('entry-move',id=entry,direction=-1)
  queue=self.store.browse({'operation':'queue','playlist':p})['items'];self.assertEqual([r['id'] for r in queue],[a,a,b])
  self.put('progress',id=a,entry=entry,playlist=p,position=42,duration=100,completed=False)
  queue=self.store.browse({'operation':'queue','playlist':p})['items'];self.assertEqual([r['position'] for r in queue],[0,42,0])
  self.store.close();self.store=Collections(self.temp.name);self.assertEqual(self.store.browse({'operation':'queue','playlist':p})['playlist']['resume_entry'],entry)
  self.put('entry-remove',id=entry);self.assertEqual(self.store.browse({})['total'],2)
  self.put('playlist-delete',id=p);self.assertEqual(self.store.browse({})['total'],2)
 def test_bad_entry_progress_rolls_back(self):
  a=self.item();b=self.item('https://vimeo.com/76979871');p=self.put('playlist-save',name='List')['id'];self.put('playlist-add',id=b,playlist=p)
  entry=self.store.browse({'operation':'queue','playlist':p})['items'][0]['entry_id']
  with self.assertRaises(CollectionError):self.put('progress',id=a,playlist=p,entry=entry,position=10)
  self.assertEqual(self.store.get(a)['position'],0)
 def test_tags_are_shared_normalized_filterable_and_preserved(self):
  a=self.item(title='Treino',tags=['workout','Exercício','exercicio','Mobilidade']);b=self.item('https://vimeo.com/76979871',title='Outro',tags=['EXERCICIO'])
  rows=self.store.browse({});self.assertEqual(len(rows['tags']),3);exercise=next(t for t in rows['tags'] if t['name']=='Exercício')
  self.assertEqual(self.store.browse({'tag':exercise['id']})['total'],2)
  self.assertEqual(self.store.browse({'q':'Mobilidade'})['total'],1)
  self.assertEqual(len(self.store.get(a)['tags']),3)
  self.item(title='Treino atualizado');self.assertEqual(len(self.store.get(a)['tags']),3)
  self.item(title='Treino atualizado',tags=[]);self.assertEqual(self.store.get(a)['tags'],[]);self.assertEqual(self.store.browse({'tag':exercise['id']})['total'],1)
 def test_title_worker_fills_imported_name_without_overwriting_manual_edit(self):
  with patch('collections_store.metadata',return_value={'title':'Título da origem','author':'Autor','thumbnail':''}):
   self.put('import',items=[YT]);id=source_url(YT)['id']
   for _ in range(100):
    if self.store.get(id)['title']=='Título da origem':break
    time.sleep(.01)
   self.assertEqual(self.store.get(id)['title'],'Título da origem')
   self.put('item-save',url=YT,title='Meu título',tags=['Treino'])
   self.assertEqual(self.store.get(id)['title'],'Meu título');self.assertEqual(self.store.get(id)['tags'][0]['name'],'Treino')
 def test_import_with_invalid_tags_rolls_back_all_entries(self):
  with self.assertRaises(CollectionError):self.put('import',items=[{'url':YT,'title':'Primeiro','tags':['Bom']},{'url':'https://vimeo.com/76979871','tags':{'bad':'value'}}])
  self.assertEqual(self.store.browse({})['total'],0)

 def test_tag_manager_renames_globally_without_losing_video_data(self):
  tag=self.put('tag-save',name='Workout')['id'];self.assertEqual(self.store.browse({})['tags'][0]['count'],0)
  a=self.item(title='A',tags=['workout']);b=self.item('https://vimeo.com/76979871',title='B',tags=['Workout'])
  self.put('favorite',id=a,favorite=True);self.put('progress',id=a,position=5,duration=30)
  self.put('tag-save',id=tag,name='Mobilidade')
  self.assertEqual(self.store.get(a)['tags'][0]['name'],'Mobilidade');self.assertEqual(self.store.get(b)['tags'][0]['id'],tag)
  with self.assertRaises(CollectionError):self.put('tag-save',name='mobilidade')
  self.put('tag-delete',id=tag);self.assertEqual(self.store.get(a)['tags'],[]);self.assertTrue(self.store.get(a)['favorite']);self.assertEqual(self.store.get(a)['position'],5);self.assertEqual(self.store.browse({})['total'],2)

 def test_urls_and_invalid_values(self):
  for url in ('file:///private','http://localhost/v.mp4','https://127.0.0.1/x','https://user:pass@youtube.com/watch?v=M7lc1UVf-VE','https://youtube.com/channel/test','https://[::1]/x','https://example.com:9000/x'):
   with self.assertRaises(CollectionError):source_url(url)
  self.assertEqual(source_url('https://facebook.com/someone/videos/123456')['url'],'https://www.facebook.com/watch/?v=123456')
  id=self.item()
  with self.assertRaises(CollectionError):self.put('progress',id=id,position=float('nan'))

class HTTPTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.server=PortalServer(dict(host='127.0.0.1',port=0,network=ipaddress.ip_network('127.0.0.0/24'),runtime_path=self.temp.name,switch_delay_ms=1000,player_solution='ffmpeg'),[],{},'test')
  self.url='http://127.0.0.1:'+str(self.server.server_port);threading.Thread(target=self.server.serve_forever,daemon=True).start();self.http=urllib.request.build_opener(urllib.request.ProxyHandler({}))
 def tearDown(self):self.server.shutdown();self.server.server_close();self.temp.cleanup()
 def request(self,path,data=None,headers=None):
  req=urllib.request.Request(self.url+path,data=json.dumps(data).encode() if data is not None else None,headers=headers or {})
  try:return self.http.open(req,timeout=5)
  except urllib.error.HTTPError as e:return e
 def test_private_api_and_isolated_public_wrapper(self):
  with self.request('/api/collections',headers={'Origin':'https://evil.example'}) as r:self.assertEqual(r.status,403)
  with self.request('/api/collections',{'operation':'item-save','url':YT}) as r:self.assertEqual(r.status,403)
  with self.request('/api/collections',{'operation':'item-save','url':YT},{'X-MAG-Action':self.server.action_token}) as r:self.assertEqual(r.status,200)
  with self.request('/api/collections') as r:self.assertEqual(json.load(r)['total'],1)
  with self.request('/collections/player',headers={'Origin':'null','Sec-Fetch-Site':'cross-site'}) as r:
   self.assertEqual(r.status,200);self.assertIsNone(r.headers.get('X-Frame-Options'));self.assertEqual(r.headers['Referrer-Policy'],'strict-origin-when-cross-origin');self.assertIn('youtube.com',r.headers['Content-Security-Policy']);self.assertNotIn('MAG_TV_CONFIG',r.read().decode())
  with self.request('/web/') as r:self.assertEqual(r.headers['X-Frame-Options'],'DENY');self.assertNotIn('youtube',r.headers['Content-Security-Policy'])
  with self.request('/web/collections/') as r:self.assertEqual(r.status,200);self.assertIn("frame-src 'self'",r.headers['Content-Security-Policy'])
  with self.request('/api/collections',headers={'Host':'evil.example'}) as r:self.assertEqual(r.status,403)

 def test_tv_and_mag_are_readers_with_favorites_and_progress(self):
  headers={'X-MAG-Action':self.server.action_token}
  with self.request('/api/collections',{'operation':'item-save','url':YT,'title':'Test','client':'web'},headers) as r:id=json.load(r)['id']
  for client in ('tv','mag'):
   with self.request('/api/collections',{'operation':'tag-save','name':'Blocked','client':client},headers) as r:self.assertEqual(r.status,403)
   with self.request('/api/collections',{'operation':'item-delete','id':id,'client':client},headers) as r:self.assertEqual(r.status,403)
   with self.request('/api/collections',{'operation':'favorite','id':id,'favorite':True,'client':client},headers) as r:self.assertEqual(r.status,200)
   with self.request('/api/collections',{'operation':'progress','id':id,'position':5,'duration':30,'client':client},headers) as r:self.assertEqual(r.status,200)
  self.server.tv_access.key='a'*64
  tv=dict(headers,**{'X-MAG-TV':'a'*64,'Origin':'null'})
  with self.request('/api/collections',{'operation':'tag-save','name':'Spoof web','client':'web'},tv) as r:self.assertEqual(r.status,403)
  self.assertEqual(self.server.collections.get(id)['position'],5);self.assertTrue(self.server.collections.get(id)['favorite'])

if __name__=='__main__':unittest.main()
