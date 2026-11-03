import io
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import facebook_metadata as fb
from collections_store import Collections,CollectionError

URL='https://www.facebook.com/watch/?v=123456'
def poster():
 out=io.BytesIO();Image.new('RGB',(360,640),'teal').save(out,'PNG');return out.getvalue()
def page(extra=''):
 return ('<meta property="og:type" content="video.other"><meta property="og:title" content="Treino &amp; mobilidade"><meta property="og:image" content="https://scontent.example.fbcdn.net/image.jpg">'+extra).encode()

class FacebookMetadataTests(unittest.TestCase):
 def test_public_cover_is_decoded_and_ratio_preserved(self):
  with patch.object(fb,'fetch',side_effect=[page(),poster()]) as fetch:
   data=fb.metadata(URL)
  self.assertEqual(data['title'],'Treino & mobilidade');self.assertEqual(data['aspect_ratio'],9/16)
  self.assertEqual(Image.open(io.BytesIO(data['_cover'])).size,(360,640))
  self.assertEqual(fetch.call_args_list[1].args[1:],(5000000,True))
 def test_explicit_video_dimensions_win_over_poster(self):
  with patch.object(fb,'fetch',side_effect=[page('<meta property="og:video:width" content="1920"><meta property="og:video:height" content="1080">'),poster()]):data=fb.metadata(URL)
  self.assertAlmostEqual(data['aspect_ratio'],16/9)
 def test_unavailable_private_and_invalid_metadata_do_not_replace_data(self):
  for failure in (OSError('offline'),ValueError('redirect')):
   with patch.object(fb,'fetch',side_effect=failure):self.assertEqual(fb.metadata(URL),{})
  with patch.object(fb,'fetch',return_value=b'<meta property="og:type" content="website">'):self.assertEqual(fb.metadata(URL),{})
  with patch.object(fb,'fetch',side_effect=[page(),b'not an image']):self.assertEqual(fb.metadata(URL),{})
 def test_fetch_and_redirects_only_allow_known_public_hosts(self):
  for url in ('http://facebook.com/watch/','https://127.0.0.1/v','https://facebook.com.evil.test/v','https://user:pass@facebook.com/v','https://facebook.com:8000/v','https://www.facebook.com/login/?next=video','https://www.facebook.com/checkpoint/abc'):
   self.assertFalse(fb.allowed(url))
   with self.assertRaises(ValueError):fb.fetch(url,100)
   with self.assertRaises(ValueError):fb.PublicRedirect().redirect_request(None,None,302,'',{},url)
  for url in ('https://evilfbcdn.net/image','https://facebook.com/image','https://127.0.0.1/image','http://x.fbcdn.net/image'):
   self.assertFalse(fb.allowed(url,True))
  self.assertTrue(fb.allowed(URL));self.assertTrue(fb.allowed('https://x.fbcdn.net/image',True))
 def test_untrusted_image_is_not_requested(self):
  with patch.object(fb,'fetch',return_value=page().replace(b'https://scontent.example.fbcdn.net/image.jpg',b'https://127.0.0.1/private')) as fetch:
   result=fb.metadata(URL)
  self.assertNotIn('_cover',result);self.assertEqual(fetch.call_count,1)

class FacebookStoreTests(unittest.TestCase):
 def test_cover_persists_and_does_not_change_organization_or_manual_title(self):
  with tempfile.TemporaryDirectory() as temp,patch('collections_store.metadata',return_value={}):
   store=Collections(temp)
   try:
    id=store.update(dict(operation='item-save',url=URL,title='Meu treino',tags=['ForÃ§a']))['id']
    store.update(dict(operation='favorite',id=id,favorite=True));store.update(dict(operation='progress',id=id,position=12,duration=120))
    with store.lock,store.db:store._apply_metadata(id,dict(title='TÃ­tulo da origem',_cover=poster(),aspect_ratio=9/16))
    before=store.get(id);self.assertEqual(before['title'],'Meu treino');self.assertTrue(before['thumbnail'].startswith('/collections/image/'))
    with store.lock,store.db:store._apply_metadata(id,{})
    self.assertEqual(store.get(id),before);self.assertEqual(store.image(id),poster())
    json.dumps(store.browse({}))
    store.close();store=Collections(temp)
    row=store.get(id);self.assertTrue(row['favorite']);self.assertEqual(row['position'],12);self.assertEqual(row['tags'][0]['name'],'ForÃ§a');self.assertEqual(row['aspect_ratio'],9/16)
    self.assertEqual(store.image(id),poster())
    store.update(dict(operation='item-delete',id=id))
    with self.assertRaises(CollectionError):store.image(id)
   finally:store.close()
 def test_old_database_migrates_without_losing_items(self):
  with tempfile.TemporaryDirectory() as temp,patch('collections_store.metadata',return_value={}):
   store=Collections(temp);id=store.update(dict(operation='item-save',url=URL,title='Guardado'))['id'];store.close()
   db=sqlite3.connect(Path(temp)/'collections.sqlite');db.execute('ALTER TABLE items DROP COLUMN aspect_ratio');db.commit();db.close()
   store=Collections(temp)
   try:self.assertEqual(store.get(id)['title'],'Guardado');self.assertEqual(store.get(id)['aspect_ratio'],0)
   finally:store.close()

if __name__=='__main__':unittest.main()
