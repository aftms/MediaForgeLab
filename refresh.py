"""Transactional metadata refresh. No media requests, no credential logging."""
import copy
import json
from pathlib import Path
import re
import threading
import time
from catalog import Catalog, country_for, family_key
from provider import Provider
from storage import json_bytes, read_json, recover, atomic_batch


def clean(value, limit=1500):
    return re.sub(r'[\x00-\x1f\x7f]', ' ', str(value or ''))[:limit]


def normalize(provider, kind, categories, rows):
    if not isinstance(categories, list) or not categories or not isinstance(rows, list) or not rows:
        raise ValueError('Empty or invalid metadata')
    category_map = {}
    for category in categories:
        if not isinstance(category, dict) or not str(category.get('category_id','')).isdigit():
            raise ValueError('Invalid category')
        category_map[str(category['category_id'])] = clean(category.get('category_name') or 'Outros',150)
    result = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Invalid entry')
        identifier = str(row.get('series_id' if kind == 'series' else 'stream_id',''))
        if not identifier.isdigit() or not row.get('name'):
            raise ValueError('Invalid identifier')
        if re.match(r'^\s*#{3,}', str(row['name'])):
            continue
        ids = row.get('category_ids') or []
        if not isinstance(ids, list):
            ids = [ids]
        ids = list(dict.fromkeys(str(v) for v in [row.get('category_id')] + ids if v is not None))
        groups = list(dict.fromkeys(category_map[v] for v in ids if v in category_map)) or ['Outros']
        extension = str(row.get('container_extension') or ('ts' if kind == 'tv' else 'mp4'))
        if not re.fullmatch(r'[A-Za-z0-9]{1,8}', extension):
            raise ValueError('Invalid extension')
        item = dict(provider_id=identifier, kind=kind, name=clean(row['name'],180),
                    group=groups[0], groups=groups, category_ids=ids,
                    country=country_for(groups[0]) if kind == 'tv' else '', extension=extension,
                    cover=clean(row.get('stream_icon') or row.get('cover'),2000),
                    epg_id=clean(row.get('epg_channel_id'),200))
        for field in ('plot','year','releaseDate','rating','genre','cast','director','last_modified','added'):
            item[field] = clean(row.get(field))
        if kind != 'series':
            item['url'] = provider.media_url('live' if kind == 'tv' else 'movie', identifier, extension)
        result[identifier] = item  # Same typed provider ID updates metadata, never adds a duplicate.
    if not result:
        raise ValueError('No content entries')
    return result


def merge(old, incoming):
    """Keep order, stable portal IDs and favorite family keys across renames."""
    rows, seen, added, changed = [], set(), {}, {}
    next_tv = max([int(i['id']) for i in old if i['kind']=='tv' and str(i['id']).isdigit()] or [0])+1
    for kind in ('tv','movie','series'):
        added[kind] = changed[kind] = 0
        for previous in (i for i in old if i['kind']==kind):
            pid = str(previous.get('provider_id',''))
            if not pid.isdigit() or (kind,pid) in seen:
                continue
            seen.add((kind,pid))
            fresh = incoming[kind].get(pid)
            item = dict(previous)
            if fresh:
                changed[kind] += int(any(previous.get(k) != v for k,v in fresh.items()))
                item.update(fresh)
            item['favorite_key'] = previous.get('favorite_key') or previous.get('key') or family_key(item)
            rows.append({k:v for k,v in item.items() if not k.startswith('_') and k not in ('key','quality')})
        for pid, fresh in incoming[kind].items():
            if (kind,pid) in seen:
                continue
            item = dict(fresh, id=str(next_tv) if kind=='tv' else ('m' if kind=='movie' else 's')+pid)
            if kind=='tv':
                next_tv += 1
            rows.append(item)
            added[kind] += 1
    # New quality variants use the existing station's preserved favorite family.
    families = {family_key(i):i['favorite_key'] for i in rows if i.get('favorite_key')}
    for item in rows:
        item.setdefault('favorite_key', families.get(family_key(item), family_key(item)))
    return rows, dict(added=added, changed=changed)


def m3u(rows):
    def attr(value):
        return clean(value,2000).replace('"', "'")
    lines = ['#EXTM3U']
    for item in rows:
        if not item.get('url'):
            continue
        lines += ['#EXTINF:-1 tvg-id="%s" tvg-logo="%s" group-title="%s",%s' %
                  (attr(item.get('epg_id','')), attr(item.get('cover','')), attr(item['group']), clean(item['name'],180)), item['url']]
    return ('\n'.join(lines)+'\n').encode('utf-8')


def validate_file(target, temporary):
    if target.suffix == '.json':
        value = json.loads(temporary.read_text(encoding='utf-8'))
        if not value:
            raise ValueError('Empty catalog')
    elif target.suffix == '.m3u':
        lines = temporary.read_text(encoding='utf-8').splitlines()
        if len(lines)<3 or lines[0]!='#EXTM3U' or len(lines)%2!=1:
            raise ValueError('Invalid playlist')
        seen = set()
        for i in range(1,len(lines),2):
            if not lines[i].startswith('#EXTINF:-1 ') or not lines[i+1].startswith(('http://','https://')) or re.search(r'\s',lines[i+1]):
                raise ValueError('Invalid playlist entry')
            if lines[i+1] in seen:
                raise ValueError('Duplicate playlist entry')
            seen.add(lines[i+1])


class RefreshManager:
    def __init__(self, server, runtime, export_dir, provider_factory=Provider, snapshot_info=None):
        self.server, self.runtime, self.export_dir = server, Path(runtime), Path(export_dir)
        self.factory = provider_factory
        self.lock = threading.RLock()
        self.files_lock = threading.RLock()
        self.thread = None
        self.state = read_json(self.runtime/'refresh-status.json', {}) or {}
        snapshot = snapshot_info
        if snapshot:
            self.state.update(last_success=snapshot['updated'],summary=snapshot['summary'])
        self.state.update(running=False, stage='idle')
        self.attach(server.catalog)

    def attach(self, catalog):
        catalog.episode_loader = self.load_episodes

    def restore_progress_episodes(self, identifiers):
        """Rehydrate only watched episodes from disk, without supplier requests."""
        missing = {i for i in identifiers if i.startswith('e') and i not in self.server.catalog.by_id}
        if not missing:
            return
        with self.files_lock:
            cached = read_json(self.export_dir/'catalogo-vod'/'portal-episodios.json', {}) or {}
        catalog = self.server.catalog
        with catalog.lock:
            for series_id, block in cached.items():
                if series_id not in catalog.by_id:
                    continue
                for item in block.get('items', []):
                    if item.get('id') in missing and item.get('kind') == 'episode':
                        catalog.add(item)

    def status(self):
        with self.lock:
            return copy.deepcopy(self.state)

    def source(self):
        configured = read_json(self.runtime/'source.json', {})
        return self.factory(configured['url']) if configured else self.server.catalog.provider

    def source_info(self):
        provider = self.source()
        return {'configured':bool(provider), 'server':provider.origin if provider else ''}

    def set_source(self, url):
        if not isinstance(url,str) or len(url)>4096 or not url.split('?',1)[0].endswith('/get.php'):
            raise ValueError('Invalid source URL')
        provider = self.factory(url)
        with self.lock:
            if self.state.get('running'):
                raise ValueError('Refresh in progress')
            with self.files_lock:
                atomic_batch({self.runtime/'source.json':json_bytes({'url':provider.source_url()})},self.runtime/'source-journal.json')
        return self.source_info()

    def start(self):
        with self.lock:
            if self.state.get('running'):
                return self.status()
            self.state.update(running=True,stage='A consultar canais, filmes e séries',error='')
            self.thread = threading.Thread(target=self.run,daemon=True)
            self.thread.start()
            return self.status()

    def run(self):
        try:
            provider = self.source()
            if provider is None:
                raise ValueError('Missing source')
            incoming = {}
            for kind, prefix, listing in [('tv','live','get_live_streams'),('movie','vod','get_vod_streams'),('series','series','get_series')]:
                with self.lock:
                    self.state['stage'] = 'A verificar '+{'tv':'canais','movie':'filmes','series':'séries'}[kind]
                categories = provider.fetch('get_'+prefix+'_categories')
                incoming[kind] = normalize(provider,kind,categories,provider.fetch(listing))
            old = self.server.catalog
            rows, summary = merge(old.items,incoming)
            updated = time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
            snapshot = dict(version=1,updated=updated,source=provider.source_url(),items=rows,summary=summary)
            cfg = dict(self.server.config, catalog_cache=None, _playlist_media=[], movies_playlist=None)
            candidate = Catalog([],cfg)
            candidate.provider = provider
            for row in rows:
                candidate.add(row)
            candidate.library_status = {'tv':'ok','movies':'ok','series':'ok'}
            self.attach(candidate)
            files = {self.runtime/'catalog-current.json':json_bytes(snapshot)}
            for kind, name in [('tv','canais'),('movie','filmes'),('series','series')]:
                subset = [i for i in rows if i['kind']==kind]
                files[self.export_dir/'catalogo-vod'/('portal-'+name+'-completos.json')] = json_bytes(subset)
                if kind!='series':
                    files[self.export_dir/(name+'-completos.m3u')] = m3u(subset)
            with self.lock:
                self.state['stage'] = 'A validar e guardar o catálogo'
            # Favorites can change during a download; serialize only publication.
            with self.files_lock, self.server.catalog_lock:
                old = self.server.catalog
                with old.lock:
                    candidate.favorites = set(old.favorites)
                    # Keep existing episode IDs usable by open screens and players.
                    for item in list(old.by_id.values()):
                        if item['kind']=='episode':
                            candidate.add(item)
                    atomic_batch(files,self.runtime/'update-journal.json',validate_file)
                    self.server.catalog = candidate
            with self.lock:
                self.state.update(running=False,stage='Concluído',last_success=updated,summary=summary,error='')
                try:
                    atomic_batch({self.runtime/'refresh-status.json':json_bytes(self.state)},self.runtime/'status-journal.json')
                except Exception:
                    pass  # Snapshot remains the authoritative success record.
        except Exception as error:
            with self.lock:
                failed_stage = self.state.get('stage','')
                self.state.update(running=False,stage='Falha',failed_stage=failed_stage,error_kind=type(error).__name__,error='Não foi possível atualizar. O catálogo anterior foi preservado. Verifique a origem e a ligação e tente novamente.')

    def load_episodes(self, catalog, series):
        """Only the selected series; retain downloaded episodes on empty/failure."""
        path = self.export_dir/'catalogo-vod'/'portal-episodios.json'
        with self.files_lock:
            cached = read_json(path,{}) or {}
            previous = cached.get(series['id'],{})
        try:
            info = catalog.provider.fetch('get_series_info',series_id=series['provider_id'],timeout=12)
            if not isinstance(info,dict) or not isinstance(info.get('episodes'),dict) or not info['episodes']:
                raise ValueError('Empty series')
            rows = {}
            for season, entries in info['episodes'].items():
                if not isinstance(entries,list):
                    raise ValueError('Invalid episodes')
                for entry in entries:
                    pid = str(entry.get('id',''))
                    extension = str(entry.get('container_extension') or 'mp4')
                    url = catalog.provider.media_url('series',pid,extension)
                    actual_season = str(entry.get('season') if entry.get('season') is not None else season)
                    number = str(entry.get('episode_num',''))
                    rows[pid] = dict(id='e'+pid,provider_id=pid,kind='episode',series_id=series['id'],season=actual_season,
                        episode_num=number,extension=extension,url=url,group=series['name'],
                        name='T%s E%s · %s' % (actual_season,number,clean(entry.get('title') or 'Episódio',150)),
                        plot=clean((entry.get('info') or {}).get('plot')),cover=clean((entry.get('info') or {}).get('movie_image'),2000))
            if not rows:
                raise ValueError('Empty episodes')
            merged = {i['provider_id']:i for i in previous.get('items',[])}
            added = len(set(rows)-set(merged))
            merged.update(rows)
            def numeric(value):
                return int(value) if str(value).isdigit() else 999999
            items = sorted(merged.values(),key=lambda i:(numeric(i['season']),numeric(i['episode_num']),i['id']))
            with self.files_lock:
                cached = read_json(path,{}) or {}
                cached[series['id']] = dict(items=items,checked=int(time.time()),added=added)
                exports = [item for block in cached.values() for item in block['items']]
                atomic_batch({path:json_bytes(cached),self.export_dir/'series-episodios.m3u':m3u(exports)},self.runtime/'episode-journal.json',validate_file)
            return items, 'ok', added
        except Exception:
            if previous.get('items'):
                return previous['items'], 'cached_after_error', 0
            raise ValueError('Episodes temporarily unavailable') from None
