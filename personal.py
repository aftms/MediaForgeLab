"""Private personal library: atomic metadata scans, shared albums and read-only media."""
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import threading
import time
import uuid
from types import SimpleNamespace
from PIL import Image, ImageOps
from onedrive import OneDrive, CloudError
from media import MediaManager, MediaError

IMAGE_EXT={'.jpg','.jpeg','.png','.gif','.bmp','.webp','.heic','.heif','.tif','.tiff','.avif'}
VIDEO_EXT={'.mp4','.mov','.mkv','.m4v','.avi','.webm','.wmv','.mts','.m2ts'}

def identifier(drive,item):return 'p'+hashlib.sha256((drive+'\0'+item).encode()).hexdigest()[:32]

class PersonalLibrary:
    def __init__(self,root,cloud=None):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
        self.cloud=cloud or OneDrive(self.root)
        self.worker=None;self.lock=threading.RLock();self.image_lock=threading.Lock();self.closed=threading.Event()
        self.db=sqlite3.connect(str(self.root/'library.db'),check_same_thread=False)
        self.db.row_factory=sqlite3.Row
        self.db.executescript('PRAGMA journal_mode=WAL;\nCREATE TABLE IF NOT EXISTS roots(id TEXT PRIMARY KEY,drive TEXT,remote TEXT,name TEXT,updated TEXT);\nCREATE TABLE IF NOT EXISTS items(id TEXT PRIMARY KEY,drive TEXT,remote TEXT,name TEXT,kind TEXT,folder TEXT,date TEXT,year TEXT,etag TEXT,mime TEXT,duration REAL,width INTEGER,height INTEGER,favorite INTEGER DEFAULT 0,position REAL DEFAULT 0,completed INTEGER DEFAULT 0,available INTEGER DEFAULT 1);\nCREATE TABLE IF NOT EXISTS membership(root TEXT,item TEXT,PRIMARY KEY(root,item));\nCREATE TABLE IF NOT EXISTS albums(id TEXT PRIMARY KEY,name TEXT NOT NULL);\nCREATE TABLE IF NOT EXISTS album_items(album TEXT,item TEXT,PRIMARY KEY(album,item));\nCREATE INDEX IF NOT EXISTS items_kind ON items(kind,year);\n')
        self.db.commit();last=self.db.execute('SELECT max(updated) FROM roots').fetchone()[0] or '';self.scan=dict(running=False,seen=0,added=0,updated=0,error='',last_success=last)
    def close(self):
        self.closed.set();self.cloud.close()
        if self.worker and self.worker.is_alive():self.worker.join(timeout=30)
        if not self.worker or not self.worker.is_alive():
            with self.lock:self.db.close()
    def status(self):
        with self.lock:
            rows=self.db.execute('SELECT kind,count(*) n FROM items WHERE available=1 GROUP BY kind').fetchall()
            return dict(connection=self.cloud.state(),scan=dict(self.scan),counts={r['kind']:r['n'] for r in rows},roots=[dict(r) for r in self.db.execute('SELECT id,name,updated FROM roots')])
    def add_root(self,remote):
        drive=self.cloud.config.get('drive_id')
        if not drive:raise CloudError('Ligue o OneDrive antes de escolher uma pasta.',401)
        d=self.cloud.get(self.cloud.item_path(drive,remote))
        if 'folder' not in d:raise CloudError('Escolha uma pasta do OneDrive.')
        rid=identifier(drive,d['id'])
        with self.lock,self.db:
            self.db.execute('INSERT INTO roots(id,drive,remote,name,updated) VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name',(rid,drive,d['id'],d['name'],''))
        return dict(id=rid,name=d['name'])
    def start_scan(self):
        with self.lock:
            if self.scan['running']:return dict(self.scan)
            roots=[dict(r) for r in self.db.execute('SELECT * FROM roots')]
            if not roots:raise CloudError('Escolha primeiro uma pasta para a biblioteca.')
            if not self.cloud.state()['connected']:raise CloudError('Ligue primeiro o OneDrive.',401)
            self.scan.update(running=True,seen=0,added=0,updated=0,error='')
            self.worker=threading.Thread(target=self._scan,args=(roots,),daemon=True);self.worker.start()
            return dict(self.scan)
    def _collect(self,root):
        root_path=self.cloud.item_path(root['drive'],root['remote'])
        tag=self.cloud.get(root_path+'?$select=id,cTag').get('cTag')
        queue=[(root['remote'],root['name'])];visited=set();items={}
        while queue:
            parent,folder=queue.pop(0)
            if parent in visited:continue
            visited.add(parent)
            path=self.cloud.item_path(root['drive'],parent)+'/children?$top=200'
            pages=set()
            while path:
                if self.closed.is_set():raise CloudError('Atualização cancelada. Catálogo preservado.')
                if path in pages:raise CloudError('Paginação do OneDrive repetida. Catálogo preservado.',502)
                pages.add(path);d=self.cloud.get(path)
                if not isinstance(d.get('value'),list):raise CloudError('Catálogo OneDrive inválido. Dados anteriores preservados.',502)
                for row in d['value']:
                    if not isinstance(row,dict) or not row.get('id') or not isinstance(row.get('name'),str):raise CloudError('Entrada OneDrive inválida.',502)
                    if 'remoteItem' in row:continue # Cross-drive shortcuts are selected as explicit roots in a later version.
                    if 'folder' in row:queue.append((row['id'],folder+'/'+row['name']));continue
                    ext=Path(row['name']).suffix.lower()
                    kind='photo' if 'image' in row or ext in IMAGE_EXT else 'video' if 'video' in row or ext in VIDEO_EXT else None
                    if not kind:continue
                    date=str((row.get('photo') or {}).get('takenDateTime') or row.get('createdDateTime') or row.get('lastModifiedDateTime') or '')
                    year=date[:4] if date[:4].isdigit() else ''
                    info=row.get('video') or row.get('image') or {}
                    i=dict(id=identifier(root['drive'],row['id']),drive=root['drive'],remote=row['id'],name=row['name'][:500],kind=kind,folder=folder,date=date,year=year,etag=str(row.get('eTag','')),mime=(row.get('file') or {}).get('mimeType',''),duration=max(0,float(info.get('duration',0) or 0)/1000),width=int(info.get('width',0) or 0),height=int(info.get('height',0) or 0))
                    items[i['id']]=i
                    if len(items)>250000:raise CloudError('A pasta ultrapassou o limite desta primeira versão. Escolha subpastas menores.')
                with self.lock:self.scan['seen']=len(items)
                path=d.get('@odata.nextLink')
        if tag and self.cloud.get(root_path+'?$select=id,cTag').get('cTag')!=tag:
            raise CloudError('A pasta foi alterada durante a atualização. Catálogo preservado; tente novamente.',409)
        return items
    def _scan(self,roots):
        try:
            # All roots are staged before any catalog write: partial network failure changes nothing.
            staged=[(r,self._collect(r)) for r in roots]
            now=time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime())+' UTC'
            with self.lock,self.db:
                for root,rows in staged:
                    previous=self.db.execute('SELECT count(*) FROM membership WHERE root=?',(root['id'],)).fetchone()[0]
                    if previous and not rows:raise CloudError('A pasta devolveu uma lista vazia. O catálogo anterior foi preservado.',502)
                for root,rows in staged:
                    self.db.execute('DELETE FROM membership WHERE root=?',(root['id'],))
                    for row in rows.values():
                        existing=self.db.execute('SELECT etag,name,folder FROM items WHERE id=?',(row['id'],)).fetchone()
                        self.scan['added']+=int(existing is None)
                        self.scan['updated']+=int(existing is not None and (existing['etag']!=row['etag'] or existing['name']!=row['name'] or existing['folder']!=row['folder']))
                        fields=list(row);assign=','.join(f+'=excluded.'+f for f in fields if f!='id')
                        self.db.execute('INSERT INTO items('+','.join(fields)+') VALUES('+','.join('?' for _ in fields)+') ON CONFLICT(id) DO UPDATE SET '+assign+',available=1',tuple(row.values()))
                        self.db.execute('INSERT OR IGNORE INTO membership(root,item) VALUES(?,?)',(root['id'],row['id']))
                    self.db.execute('UPDATE roots SET updated=? WHERE id=?',(now,root['id']))
                self.db.execute('UPDATE items SET available=0 WHERE id NOT IN(SELECT item FROM membership)')
                self.scan['last_success']=now
        except CloudError as e:
            with self.lock:self.scan.update(error=str(e),added=0,updated=0)
        except Exception:
            with self.lock:self.scan.update(error='Não foi possível atualizar. O catálogo anterior foi preservado.',added=0,updated=0)
        finally:
            with self.lock:self.scan['running']=False
    def get(self,id):
        with self.lock:
            row=self.db.execute('SELECT * FROM items WHERE id=?',(str(id),)).fetchone()
            if row is None:raise CloudError('Conteúdo pessoal não encontrado.',404)
            return dict(row)
    def public(self,row):
        return {k:row[k] for k in ('id','name','kind','folder','date','year','duration','favorite','position','completed','available')}
    def browse(self,p):
        limit=max(1,min(60,int(p.get('limit',24))));offset=max(0,int(p.get('offset',0)))
        where=['available=1'];values=[]
        for field in ('kind','year','folder'):
            if p.get(field):where.append(field+'=?');values.append(p[field])
        if p.get('q'):where.append("(name LIKE ? ESCAPE '!' OR folder LIKE ? ESCAPE '!')");q='%'+str(p['q'])[:100].replace('!','!!').replace('%','!%').replace('_','!_')+'%';values.extend([q,q])
        if p.get('favorites')=='1':where.append('favorite=1')
        if p.get('continue')=='1':where.append('kind=\'video\' AND position>0 AND completed=0')
        if p.get('album'):where.append('id IN (SELECT item FROM album_items WHERE album=?)');values.append(p['album'])
        clause=' AND '.join(where)
        with self.lock:
            count=self.db.execute('SELECT count(*) FROM items WHERE '+clause,values).fetchone()[0]
            if p.get('anchor'):
                for rank,row in enumerate(self.db.execute('SELECT id FROM items WHERE '+clause+' ORDER BY date DESC,name,id',values)):
                    if row['id']==p['anchor']:
                        offset=(rank//limit)*limit;break
            offset=min(offset,max(0,((count-1)//limit)*limit))
            rows=self.db.execute('SELECT * FROM items WHERE '+clause+' ORDER BY date DESC,name,id LIMIT ? OFFSET ?',values+[limit,offset]).fetchall()
            years=[r[0] for r in self.db.execute("SELECT DISTINCT year FROM items WHERE available=1 AND year!='' ORDER BY year DESC")]
            folders=[r[0] for r in self.db.execute('SELECT DISTINCT folder FROM items WHERE available=1 ORDER BY folder')]
            albums=[dict(r) for r in self.db.execute('SELECT a.id,a.name,(SELECT count(*) FROM album_items m JOIN items i ON i.id=m.item WHERE m.album=a.id AND i.available=1) count FROM albums a ORDER BY a.name')]
            return dict(items=[self.public(r) for r in rows],total=count,offset=offset,years=years,folders=folders,albums=albums)
    def update(self,d):
        op=d.get('operation');id=str(d.get('id',''))
        with self.lock,self.db:
            if op=='favorite':
                self.get(id);self.db.execute('UPDATE items SET favorite=? WHERE id=?',(int(bool(d.get('favorite'))),id))
            elif op=='progress':
                row=self.get(id)
                if row['kind']!='video':raise CloudError('Só os vídeos têm progresso.')
                position=max(0,min(604800,float(d.get('position',0))));duration=max(0,min(604800,float(d.get('duration',row['duration']))))
                self.db.execute('UPDATE items SET position=?,completed=?,duration=CASE WHEN ?>0 THEN ? ELSE duration END WHERE id=?',(position,int(bool(d.get('completed'))),duration,duration,id))
            elif op in ('album-create','album-rename'):
                name=str(d.get('name','')).strip()
                if not name or len(name)>60:raise CloudError('O nome do álbum deve ter entre 1 e 60 caracteres.')
                if op=='album-create':id=uuid.uuid4().hex;self.db.execute('INSERT INTO albums VALUES(?,?)',(id,name))
                elif not self.db.execute('UPDATE albums SET name=? WHERE id=?',(name,id)).rowcount:raise CloudError('Álbum não encontrado.',404)
            elif op=='album-delete':
                self.db.execute('DELETE FROM album_items WHERE album=?',(id,));self.db.execute('DELETE FROM albums WHERE id=?',(id,))
            elif op in ('album-add','album-remove'):
                self.get(id);album=str(d.get('album',''))
                if not self.db.execute('SELECT id FROM albums WHERE id=?',(album,)).fetchone():raise CloudError('Álbum não encontrado.',404)
                if op=='album-add':self.db.execute('INSERT OR IGNORE INTO album_items VALUES(?,?)',(album,id))
                else:self.db.execute('DELETE FROM album_items WHERE album=? AND item=?',(album,id))
            else:raise CloudError('Operação pessoal desconhecida.')
        return dict(saved=True,id=id)
    def image(self,id,full=False):
        if not self.cloud.state()['connected']:raise CloudError('Ligue o OneDrive para ver as imagens.',401)
        row=self.get(id)
        if not row['available']:raise CloudError('Conteúdo indisponível no OneDrive.',404)
        key=hashlib.sha256((id+row['etag']+str(full)).encode()).hexdigest()+'.jpg'
        cache=self.root/'images';cache.mkdir(exist_ok=True);path=cache/key
        with self.image_lock:
            if path.exists():path.touch();return path.read_bytes()
            try:
                original=full and row['kind']=='photo' and row['mime'] in ('image/jpeg','image/png','image/webp')
                data=self.cloud.image_bytes(row['drive'],row['remote'],original=original)
                with Image.open(io.BytesIO(data)) as image:
                    if image.width*image.height>80000000:raise CloudError('Fotografia demasiado grande para esta visualização.',413)
                    image=ImageOps.exif_transpose(image);image.thumbnail((1920,1080) if full else (360,240));out=io.BytesIO();image.convert('RGB').save(out,'JPEG',quality=85);data=out.getvalue()
            except CloudError:raise
            except Exception:raise CloudError('Formato de fotografia ainda não suportado.',415)
            path.write_bytes(data)
            files=sorted(cache.glob('*.jpg'),key=lambda f:f.stat().st_mtime,reverse=True);size=0
            for i,file in enumerate(files):
                size+=file.stat().st_size
                if i>=400 or size>128*1024*1024:file.unlink(missing_ok=True)
            return data

class PersonalLookup:
    def __init__(self,library):self.library=library;self.by_id=self
    def get(self,id,default=None):
        try:row=self.library.get(id)
        except CloudError:return default
        return dict(row,kind='movie') if row['available'] and row['kind']=='video' else default
    def play_url(self,id):
        row=self.library.get(id)
        return self.library.cloud.content_url(row['drive'],row['remote'])

class PersonalProgress:
    def __init__(self,library):self.library=library
    def get(self,id,default=None):
        try:return self.library.get(id)
        except CloudError:return default or {}

class PersonalMedia(MediaManager):
    def __init__(self,app,library):
        self.library=library
        adapter=SimpleNamespace(runtime=library.root,config=dict(app.config,media_namespace='personal',max_video_height=1080),catalog=PersonalLookup(library),progress=PersonalProgress(library))
        super().__init__(adapter)
    def open_source(self,s,url,headers,method):
        # Re-resolve expiring cloud URLs for every new range; bearer never reaches FFmpeg/TV.
        row=self.library.get(s['id'])
        url=self.library.cloud.content_url(row['drive'],row['remote'])
        import urllib.request
        return self.library.cloud.binary.open(urllib.request.Request(url,headers=headers,method=method),timeout=20)
