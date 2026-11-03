"""Private shared social-video library. No streams, credentials or account scraping."""
import hashlib
import json
import math
import re
import sqlite3
import threading
import time
import uuid
import queue
import unicodedata
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit, parse_qs, urlencode


class CollectionError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def clean(value, limit=180):
    return re.sub(r'[\x00-\x1f\x7f]', ' ', str(value or '')).strip()[:limit]


def source_url(value):
    raw = str(value or '').strip()
    if len(raw)>4096 or re.search(r'[\s\x00-\x1f\x7f]',raw):
        raise CollectionError('Link inválido.')
    try:
        u=urlsplit(raw); host=(u.hostname or '').lower(); port=u.port
    except ValueError:raise CollectionError('Link inválido.') from None
    if u.scheme not in ('http','https') or not host or u.username or u.password or port not in (None,80,443):
        raise CollectionError('Use um link público HTTP/HTTPS, sem dados de acesso.')
    if host in ('localhost',) or '.' not in host or re.fullmatch(r'[\d.:]+',host):
        raise CollectionError('Use o endereço público do vídeo.')
    q=parse_qs(u.query); parts=u.path.strip('/').split('/'); platform='link'; key=raw.split('#')[0]
    if host in ('youtube.com','www.youtube.com','m.youtube.com','music.youtube.com','youtube-nocookie.com','www.youtube-nocookie.com','youtu.be','www.youtu.be'):
        key=parts[0] if host.endswith('youtu.be') else (q.get('v',[''])[0] if u.path=='/watch' else parts[1] if len(parts)>1 and parts[0] in ('embed','shorts','live') else '')
        if not re.fullmatch(r'[A-Za-z0-9_-]{11}',key):raise CollectionError('Cole o link de um vídeo específico do YouTube.')
        platform='youtube'; raw='https://www.youtube.com/watch?v='+key
    elif host in ('facebook.com','www.facebook.com','m.facebook.com','web.facebook.com','fb.watch','www.fb.watch'):
        match=re.search(r'/(?:reel|videos)/(\d+)',u.path); key=(match[1] if match else q.get('v',[''])[0])
        if key and key.isdigit():raw='https://www.facebook.com/watch/?v='+key
        elif host.endswith('fb.watch') and parts[0]:key=parts[0];raw='https://fb.watch/'+key+'/'
        else:raise CollectionError('Cole o link do vídeo ou reel do Facebook, não de uma página.')
        platform='facebook'
    elif host in ('vimeo.com','www.vimeo.com','player.vimeo.com') and re.fullmatch(r'\d+',parts[-1]):
        platform='vimeo';key=parts[-1];raw='https://vimeo.com/'+key
    elif host in ('instagram.com','www.instagram.com'):
        platform='instagram';raw=u._replace(query='',fragment='').geturl();key=raw
    elif host=='tiktok.com' or host.endswith('.tiktok.com'):
        platform='tiktok';raw=u._replace(query='',fragment='').geturl();key=raw
    elif u.path.lower().endswith(('.mp4','.webm','.m3u8')):
        platform='direct';raw=u._replace(fragment='').geturl();key=raw
    else:raw=u._replace(fragment='').geturl();key=raw
    return dict(platform=platform,remote_id=key,url=raw,id='col-'+hashlib.sha256((platform+':'+key).encode()).hexdigest()[:24])


def metadata(url):
    s=source_url(url)
    if s['platform'] not in ('youtube','vimeo'):return {}
    # Fixed official endpoint; never fetch a user-supplied arbitrary URL.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs):return None
    try:
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
        endpoint=('https://www.youtube.com/oembed?' if s['platform']=='youtube' else 'https://vimeo.com/api/oembed.json?')+urlencode(dict(url=s['url'],format='json'))
        with opener.open(urllib.request.Request(endpoint,headers={'User-Agent':'MediaForgeLab/1.0'}),timeout=6) as response:data=json.loads(response.read(65536))
        return dict(title=clean(data.get('title')),author=clean(data.get('author_name')),
                    thumbnail=('https://i.ytimg.com/vi/'+s['remote_id']+'/mqdefault.jpg') if s['platform']=='youtube' else '')
    except Exception:return {}


class Collections:
    def __init__(self,root):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
        self.lock=threading.RLock();self.title_pending=set();self.title_attempted=set();self.title_jobs=queue.Queue();self.closed=threading.Event()
        self.db=sqlite3.connect(self.root/'collections.sqlite',check_same_thread=False)
        self.db.row_factory=sqlite3.Row
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS categories(id TEXT PRIMARY KEY,name TEXT NOT NULL,parent TEXT REFERENCES categories(id) ON DELETE RESTRICT);
        CREATE TABLE IF NOT EXISTS items(id TEXT PRIMARY KEY,platform TEXT NOT NULL,remote_id TEXT NOT NULL,url TEXT NOT NULL,title TEXT NOT NULL,author TEXT NOT NULL DEFAULT '',notes TEXT NOT NULL DEFAULT '',thumbnail TEXT NOT NULL DEFAULT '',favorite INTEGER NOT NULL DEFAULT 0,position REAL NOT NULL DEFAULT 0,duration REAL NOT NULL DEFAULT 0,completed INTEGER NOT NULL DEFAULT 0,created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS item_categories(item TEXT REFERENCES items(id) ON DELETE CASCADE,category TEXT REFERENCES categories(id) ON DELETE CASCADE,PRIMARY KEY(item,category));
        CREATE TABLE IF NOT EXISTS playlists(id TEXT PRIMARY KEY,name TEXT NOT NULL,resume_entry TEXT NOT NULL DEFAULT '');
        CREATE TABLE IF NOT EXISTS entries(id TEXT PRIMARY KEY,playlist TEXT REFERENCES playlists(id) ON DELETE CASCADE,item TEXT REFERENCES items(id) ON DELETE CASCADE,ordinal INTEGER NOT NULL,position REAL NOT NULL DEFAULT 0,duration REAL NOT NULL DEFAULT 0,completed INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS tags(id TEXT PRIMARY KEY,name TEXT NOT NULL,normalized TEXT NOT NULL UNIQUE);
        CREATE TABLE IF NOT EXISTS item_tags(item TEXT REFERENCES items(id) ON DELETE CASCADE,tag TEXT REFERENCES tags(id) ON DELETE CASCADE,PRIMARY KEY(item,tag));
        CREATE INDEX IF NOT EXISTS item_tag ON item_tags(tag,item);
        CREATE INDEX IF NOT EXISTS entries_order ON entries(playlist,ordinal);
        CREATE INDEX IF NOT EXISTS item_category ON item_categories(category,item);
        ''');self.db.commit()
        self.title_worker=threading.Thread(target=self._titles,daemon=True,name='collection-titles');self.title_worker.start()
        with self.lock:self._enqueue_titles()
    def _generic(self,row):return row['title']=='Vídeo '+row['platform'].capitalize()
    def _enqueue_titles(self):
        for row in self.db.execute("SELECT id,title,platform FROM items WHERE platform IN ('youtube','vimeo')"):
            if self._generic(row) and row['id'] not in self.title_attempted:
                self.title_attempted.add(row['id']);self.title_pending.add(row['id']);self.title_jobs.put(row['id'])
    def _titles(self):
        while not self.closed.is_set():
            try:id=self.title_jobs.get(timeout=.25)
            except queue.Empty:continue
            try:
                with self.lock:
                    if self.closed.is_set():return
                    row=self.db.execute('SELECT * FROM items WHERE id=?',(id,)).fetchone()
                    if not row or not self._generic(row):continue
                meta=metadata(row['url'])
                with self.lock:
                    if self.closed.is_set():return
                    if meta.get('title'):
                        with self.db:self.db.execute('UPDATE items SET title=?,author=?,thumbnail=? WHERE id=? AND title=?',(meta['title'],meta['author'],meta['thumbnail'],id,row['title']))
            except (OSError,ValueError,sqlite3.Error):pass
            finally:
                with self.lock:self.title_pending.discard(id)
                self.title_jobs.task_done()
    def close(self):
        self.closed.set()
        with self.lock:self.db.close()
    def require(self,table,id):
        assert table in ('items','categories','playlists','entries')
        row=self.db.execute('SELECT * FROM '+table+' WHERE id=?',(str(id),)).fetchone()
        if not row:raise CollectionError('Entrada não encontrada.',404)
        return row
    def public(self,row):
        d=dict(row)
        for field in ('position','duration','completed'):
            if 'entry_'+field in d:d[field]=d.pop('entry_'+field)
        d['categories']=[r[0] for r in self.db.execute('SELECT category FROM item_categories WHERE item=?',(d['id'],))]
        d['tags']=[dict(r) for r in self.db.execute('SELECT t.id,t.name FROM tags t JOIN item_tags it ON it.tag=t.id WHERE it.item=? ORDER BY t.name COLLATE NOCASE',(d['id'],))]
        d['title_pending']=d['id'] in self.title_pending
        d['favorite']=bool(d['favorite']);d['completed']=bool(d['completed']);return d
    def get(self,id):
        with self.lock:return self.public(self.require('items',id))
    def browse(self,p):
        with self.lock:
            categories=[dict(r) for r in self.db.execute('SELECT * FROM categories ORDER BY name COLLATE NOCASE')]
            tags=[dict(r) for r in self.db.execute('SELECT t.id,t.name,count(it.item) count FROM tags t JOIN item_tags it ON it.tag=t.id GROUP BY t.id ORDER BY t.name COLLATE NOCASE')]
            playlists=[dict(r) for r in self.db.execute('SELECT p.*,(SELECT count(*) FROM entries e WHERE e.playlist=p.id) count FROM playlists p ORDER BY name COLLATE NOCASE')]
            if p.get('operation')=='item':return self.get(p.get('id'))
            if p.get('operation')=='queue':
                playlist=dict(self.require('playlists',p.get('playlist')))
                rows=self.db.execute('SELECT i.*,e.id entry_id,e.position entry_position,e.duration entry_duration,e.completed entry_completed FROM entries e JOIN items i ON i.id=e.item WHERE e.playlist=? ORDER BY e.ordinal,e.id LIMIT 500',(playlist['id'],))
                return dict(playlist=playlist,items=[self.public(r) for r in rows])
            limit=max(1,min(60,int(p.get('limit',24))));offset=max(0,int(p.get('offset',0)));where=[];args=[];join='';order='i.title COLLATE NOCASE,i.id';fields='i.*'
            if p.get('playlist'):
                self.require('playlists',p['playlist']);join='JOIN entries e ON e.item=i.id';where.append('e.playlist=?');args.append(p['playlist']);order='e.ordinal,e.id';fields+=',e.id entry_id,e.position entry_position,e.duration entry_duration,e.completed entry_completed'
            if p.get('category'):
                self.require('categories',p['category'])
                where.append('i.id IN (WITH RECURSIVE tree(id) AS (SELECT ? UNION ALL SELECT c.id FROM categories c JOIN tree t ON c.parent=t.id) SELECT item FROM item_categories WHERE category IN (SELECT id FROM tree))');args.append(p['category'])
            if p.get('tag'):where.append('i.id IN (SELECT item FROM item_tags WHERE tag=?)');args.append(p['tag'])
            if p.get('q'):where.append('(i.title LIKE ? OR i.author LIKE ? OR i.notes LIKE ? OR i.id IN (SELECT it.item FROM item_tags it JOIN tags t ON t.id=it.tag WHERE t.name LIKE ?))');args.extend(['%'+clean(p['q'],100)+'%']*4)
            if p.get('platform'):where.append('i.platform=?');args.append(p['platform'])
            if p.get('favorites')=='1':where.append('i.favorite=1')
            if p.get('continue')=='1':where.append('i.position>0 AND i.completed=0')
            clause=' WHERE '+' AND '.join(where) if where else ''
            total=self.db.execute('SELECT count(*) FROM items i '+join+clause,args).fetchone()[0]
            offset=min(offset,max(0,(total-1)//limit*limit))
            rows=self.db.execute('SELECT '+fields+' FROM items i '+join+clause+' ORDER BY '+order+' LIMIT ? OFFSET ?',args+[limit,offset])
            return dict(items=[self.public(row) for row in rows],total=total,offset=offset,categories=categories,playlists=playlists,tags=tags)
    def save_item(self,d):
        s=source_url(d.get('url'));existing=self.db.execute('SELECT * FROM items WHERE id=?',(s['id'],)).fetchone()
        if d.get('id') and d['id']!=s['id']:raise CollectionError('Para mudar o vídeo, guarde o novo link como outra entrada.')
        title=clean(d.get('title')) or (existing['title'] if existing else 'Vídeo '+s['platform'].capitalize())
        self.db.execute('INSERT OR IGNORE INTO items(id,platform,remote_id,url,title,created) VALUES(?,?,?,?,?,?)',(s['id'],s['platform'],s['remote_id'],s['url'],title,time.time()))
        self.db.execute('UPDATE items SET title=?,notes=? WHERE id=?',(title,clean(d.get('notes',existing['notes'] if existing else ''),2000),s['id']))
        if 'categories' in d:
            cats=d['categories']
            if not isinstance(cats,list) or len(cats)>30:raise CollectionError('Selecione até 30 categorias.')
            for category in cats:self.require('categories',category)
            self.db.execute('DELETE FROM item_categories WHERE item=?',(s['id'],))
            self.db.executemany('INSERT OR IGNORE INTO item_categories VALUES(?,?)',[(s['id'],str(c)) for c in cats])
        if 'tags' in d:
            tags=d['tags']
            if not isinstance(tags,list) or len(tags)>20:raise CollectionError('Use até 20 etiquetas por vídeo.')
            values=[]
            for tag in tags:
                if not isinstance(tag,str):raise CollectionError('Etiqueta inválida.')
                name=' '.join(clean(tag,40).split())
                if not name:continue
                normalized=''.join(c for c in unicodedata.normalize('NFKD',name.casefold()) if not unicodedata.combining(c))
                found=self.db.execute('SELECT id FROM tags WHERE normalized=?',(normalized,)).fetchone()
                key=found['id'] if found else uuid.uuid4().hex
                if not found:self.db.execute('INSERT INTO tags VALUES(?,?,?)',(key,name,normalized))
                values.append(key)
            self.db.execute('DELETE FROM item_tags WHERE item=?',(s['id'],))
            self.db.executemany('INSERT OR IGNORE INTO item_tags VALUES(?,?)',[(s['id'],key) for key in values])
        return dict(id=s['id'],added=not bool(existing))
    def update(self,d):
        op=d.get('operation');id=str(d.get('id',''))
        if op=='metadata-preview':
            result=metadata(d.get('url'))
            if not result.get('title'):raise CollectionError('Não foi possível obter o título. Pode escrevê-lo manualmente.')
            return result
        # Metadata is optional and never holds a database lock during network I/O.
        meta=metadata(d.get('url')) if op=='item-save' and d.get('metadata') else {}
        with self.lock,self.db:
            if op=='item-save':
                result=self.save_item(d)
                if meta:
                    self.db.execute('UPDATE items SET author=?,thumbnail=? WHERE id=?',(meta['author'],meta['thumbnail'],result['id']))
                    if not clean(d.get('title')) and result['added']:self.db.execute('UPDATE items SET title=? WHERE id=?',(meta['title'],result['id']))
                self.db.commit();self._enqueue_titles()
                return dict(result,saved=True,item=self.get(result['id']))
            if op=='import':
                rows=d.get('items');added=0
                if not isinstance(rows,list) or not 1<=len(rows)<=100:raise CollectionError('Importe entre 1 e 100 links de cada vez.')
                for row in rows:
                    row={'url':row} if isinstance(row,str) else row
                    if not isinstance(row,dict):raise CollectionError('Entrada de importação inválida.')
                    item=dict(url=row.get('url') or row.get('source_url') or row.get('video_url'),title=row.get('title') or row.get('name'))
                    if 'tags' in row:item['tags']=row['tags']
                    elif d.get('tags'):item['tags']=d['tags']
                    if d.get('category'):item['categories']=[d['category']]
                    added+=self.save_item(item)['added']
                self.db.commit();self._enqueue_titles()
                return dict(saved=True,added=added,existing=len(rows)-added)
            if op in ('category-save','playlist-save'):
                name=clean(d.get('name'),80)
                if not name:raise CollectionError('Indique um nome.')
                table='categories' if op=='category-save' else 'playlists';new=not id;id=id or uuid.uuid4().hex
                if not new:self.require(table,id)
                if table=='categories':
                    parent=d.get('parent') or None;cursor=parent;depth=0
                    while cursor:
                        if cursor==id:raise CollectionError('Uma categoria não pode ficar dentro de si própria.')
                        depth+=1
                        if depth>12:raise CollectionError('Limite de níveis de categorias atingido.')
                        cursor=self.require('categories',cursor)['parent']
                    if self.db.execute('SELECT id FROM categories WHERE name=? COLLATE NOCASE AND parent IS ? AND id!=?',(name,parent,id)).fetchone():raise CollectionError('Já existe uma categoria com esse nome neste nível.')
                    self.db.execute('INSERT INTO categories VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,parent=excluded.parent',(id,name,parent))
                else:self.db.execute('INSERT INTO playlists(id,name) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name',(id,name))
            elif op in ('category-delete','playlist-delete','item-delete'):
                table={'category-delete':'categories','playlist-delete':'playlists','item-delete':'items'}[op];self.require(table,id)
                if table=='categories' and self.db.execute('SELECT 1 FROM categories WHERE parent=?',(id,)).fetchone():raise CollectionError('Mova ou elimine primeiro as subcategorias. Os vídeos serão preservados.')
                self.db.execute('DELETE FROM '+table+' WHERE id=?',(id,))
            elif op=='favorite':
                self.require('items',id);self.db.execute('UPDATE items SET favorite=? WHERE id=?',(int(bool(d.get('favorite'))),id))
            elif op=='playlist-add':
                self.require('items',id);playlist=str(d.get('playlist',''));self.require('playlists',playlist)
                if self.db.execute('SELECT count(*) FROM entries WHERE playlist=?',(playlist,)).fetchone()[0]>=500:raise CollectionError('A lista suporta até 500 entradas.')
                ordinal=self.db.execute('SELECT COALESCE(MAX(ordinal),0)+1 FROM entries WHERE playlist=?',(playlist,)).fetchone()[0]
                self.db.execute('INSERT INTO entries(id,playlist,item,ordinal) VALUES(?,?,?,?)',(uuid.uuid4().hex,playlist,id,ordinal))
            elif op in ('entry-remove','entry-move'):
                row=self.require('entries',id)
                if op=='entry-remove':self.db.execute('DELETE FROM entries WHERE id=?',(id,))
                else:
                    direction=int(d.get('direction',0))
                    if direction not in (-1,1):raise CollectionError('Direção inválida.')
                    ids=[r[0] for r in self.db.execute('SELECT id FROM entries WHERE playlist=? ORDER BY ordinal,id',(row['playlist'],))];index=ids.index(id);other=index+direction
                    if 0<=other<len(ids):ids[index],ids[other]=ids[other],ids[index]
                    self.db.executemany('UPDATE entries SET ordinal=? WHERE id=?',[(i,key) for i,key in enumerate(ids)])
            elif op=='progress':
                row=self.require('items',id);position=float(d.get('position',0));duration=float(d.get('duration',0))
                if not math.isfinite(position+duration) or min(position,duration)<0 or max(position,duration)>604800:raise CollectionError('Posição inválida.')
                self.db.execute('UPDATE items SET position=?,duration=CASE WHEN ?>0 THEN ? ELSE duration END,completed=? WHERE id=?',(position,duration,duration,int(bool(d.get('completed'))),id))
                if d.get('playlist') and d.get('entry'):
                    entry=self.require('entries',d['entry'])
                    if entry['item']!=id or entry['playlist']!=d['playlist']:raise CollectionError('Entrada da lista inválida.')
                    self.db.execute('UPDATE entries SET position=?,duration=CASE WHEN ?>0 THEN ? ELSE duration END,completed=? WHERE id=?',(position,duration,duration,int(bool(d.get('completed'))),entry['id']))
                    self.db.execute('UPDATE playlists SET resume_entry=? WHERE id=?',(entry['id'],entry['playlist']))
            else:raise CollectionError('Operação desconhecida.')
            return dict(saved=True,id=id)
