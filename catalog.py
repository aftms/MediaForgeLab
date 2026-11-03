"""Paged catalog, quality families, persistent household favorites and short EPG."""
import collections
import hashlib
import json
from pathlib import Path
import re
import threading
import time
import unicodedata
from urllib.parse import urlsplit
from provider import Provider, decode_epg
from channel_categories import CATEGORIES, category_hint
from storage import atomic_batch, json_bytes, recover

COUNTRIES = dict(PT='Portugal', ES='Espanha', UK='Reino Unido', IE='Irlanda', FR='França', BR='Brasil',
    DE='Alemanha', IT='Itália', NL='Países Baixos', SE='Suécia', DK='Dinamarca', NO='Noruega', FI='Finlândia',
    GR='Grécia', IS='Islândia', CA='Canadá', CY='Chipre', MX='México', AR='Argentina', US='Estados Unidos',
    AT='Áustria', CH='Suíça', BE='Bélgica', HR='Croácia', PL='Polónia', TR='Turquia', IR='Irão', AG='Afeganistão',
    HU='Hungria', RO='Roménia', SU='Suriname', AL='Albânia', RU='Rússia', IL='Israel', AU='Austrália', NZ='Nova Zelândia',
    BG='Bulgária', MA='Malta', JP='Japão', TN='Taiwan', PH='Filipinas', GE='Geórgia', AZ='Azerbaijão', UZ='Usbequistão',
    AM='Arménia', CZ='Chéquia', SR='Sérvia', BH='Bósnia e Herzegovina', MK='Macedónia do Norte', SI='Eslovénia',
    VE='Venezuela', VI='Vietname', ID='Indonésia', KR='Coreia do Sul', TH='Tailândia', CG='Montenegro', KZ='Cazaquistão',
    LT='Lituânia', HK='Hong Kong', LV='Letónia', CO='Colômbia', BO='Bolívia', PE='Peru', CL='Chile', EC='Equador',
    ARAB='Países árabes', AFR='África', ASIA='Ásia', LA='América Latina', KU='Curdo / Curdistão', EXYU='Balcãs',
    OTHER='Outros / Internacionais', SO='Somália')
QUALITY_RANK = {'FHD': 60, 'HD': 50, '4K': 45, 'SD': 40, 'UNKNOWN': 30, '8K': 10}


def normalized(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(value)).upper() if not unicodedata.combining(c))


def quality(name, group=''):
    for candidate in (name, group):
        label = normalized(candidate)
        for code, pattern in [('8K', r'\b8K\b|4320'), ('4K', r'\b4K\b|\bUHD\b|2160'),
                              ('FHD', r'\bFHD\b|FULL\s*HD|1080'), ('HD', r'\bHD\b|720'), ('SD', r'\bSD\b|576|480')]:
            if re.search(pattern, label):
                return code
    return 'UNKNOWN'


ORIGINS = {'VO':'VO · Vodafone','MEO':'MEO','NOS':'NOS','VIP':'VIP','PT':'PT · Lista geral','OTHER':'Origem não indicada'}


def origin_for(item):
    if item.get('kind') != 'tv':
        return ''
    name = normalized(item.get('name',''))
    prefix = re.match(r'^(VO|VODAFONE|MEO|NOS|VIP)\s*[:|]',name)
    if prefix:
        return 'VO' if prefix[1]=='VODAFONE' else prefix[1]
    groups = normalized(' '.join(item.get('groups') or [item.get('group','')]))
    for code, pattern in [('VO',r'\bVODAFONE\b'),('MEO',r'\bMEO\b'),('NOS',r'\bNOS\b'),('VIP',r'VIP\b')]:
        if re.search(pattern,groups):
            return code
    return 'PT' if re.match(r'^PT\s*[:|]',name) else 'OTHER'


def country_for(group):
    group = normalized(group)
    code = group.split('|', 1)[0].strip() if '|' in group else 'OTHER'
    if code == 'AR' and (re.search(r'[\u0600-\u06ff]', group) or re.search(r'SHAHID|ARAB|MBC|BEIN', group)):
        return 'ARAB'
    if code == 'HR' and 'HORSE' in group:
        return 'OTHER'
    if code == 'LA':
        for name, actual in [('COLOMBIA','CO'), ('PERU','PE'), ('CHILE','CL'), ('ECUADOR','EC')]:
            if name in group:
                return actual
    if code == 'AFR' and 'SOM' in group:
        return 'SO'
    return code if code in COUNTRIES else 'OTHER'


def family_key(item):
    if item['kind'] != 'tv':
        return item.get('series_id') if item['kind'] == 'episode' and item.get('series_id') else item['id']
    name = normalized(item['name'])
    name = re.sub(r'^(?:(?:MEO|NOS|VODAFONE|VO|VIP|PT)\s*[:|]\s*)+', '', name)
    name = re.sub(r'\b(?:8K|4K|UHD|FHD|FULL\s*HD|HD|SD|RAW|1080[PI]?|720P|2160P)\b', '', name)
    name = re.sub(r'[^\w+]+', '', name)
    return 'tv-' + hashlib.sha256((item['country'] + '|' + name).encode()).hexdigest()[:24]


def season_key(value):
    value = str(value if value is not None else '').strip()
    return str(int(value)) if value.isdigit() else value or 'unknown'


def season_order(value):
    key = season_key(value)
    return (0, int(key)) if key.isdigit() else (1, key)


def season_name(value):
    key = season_key(value)
    return 'Especiais' if key == '0' else 'Sem temporada indicada' if key == 'unknown' else 'Temporada ' + key


class Catalog:
    def __init__(self, channels, config):
        self.lock = threading.RLock()
        self.items, self.by_id = [], {}
        self.by_kind = collections.defaultdict(list)
        self.by_country = collections.defaultdict(list)
        self.by_group = collections.defaultdict(list)
        self.by_family = collections.defaultdict(list)
        self.family_categories = {}
        self.kind_counts = collections.Counter()
        self.summaries = collections.OrderedDict()
        self.provider = None
        self.favorites = set()
        self.favorites_path = Path(config['favorites_path']) if config.get('favorites_path') else None
        self.epg_cache, self.series_cache = {}, {}
        self.series_checked, self.episode_status = {}, {}
        self.episode_loader = None
        self.cache = collections.OrderedDict()
        self.library_status = {}
        for channel in channels:
            item = dict(channel, id=str(channel['id']), kind='tv', country=country_for(channel['group']))
            try:
                item['provider_id'] = Path(urlsplit(item['url']).path).stem
                if self.provider is None and config.get('provider_metadata'):
                    self.provider = Provider(item['url'])
            except ValueError:
                pass
            self.add(item)
        for item in config.get('_playlist_media', []):
            self.add(item)
        if config.get('catalog_cache'):
            try:
                library = json.loads(Path(config['catalog_cache']).read_text(encoding='utf-8'))
                self.library_status = library.get('status', {})
                for kind in ('movies', 'series'):
                    if kind == 'movies' and config.get('movies_playlist'):
                        continue
                    for item in library.get(kind, []):
                        self.add(item)
            except (OSError, ValueError, TypeError):
                self.library_status = {'movies': 'not_loaded', 'series': 'not_loaded'}
        if self.favorites_path:
            recover(self.favorites_path.with_suffix('.journal.json'))
            self.favorites = self.read_favorites()

    def read_favorites(self):
        try:
            value = json.loads(self.favorites_path.read_text(encoding='utf-8'))
        except FileNotFoundError:
            return set()
        except ValueError as error:
            raise OSError('Invalid favorites file; preserved for recovery') from error
        if not isinstance(value, list) or any(not isinstance(key, str) or not key or len(key) > 200 for key in value):
            raise OSError('Invalid favorites file; preserved for recovery')
        return set(value)

    def add(self, source):
        item = dict(source)
        item['id'] = str(item['id'])
        item.setdefault('country', '')
        item['quality'] = quality(item['name'], item['group'])
        item['origin'] = origin_for(item)
        item['key'] = item.get('favorite_key') or family_key(item)
        if item['kind']=='tv':
            category, priority = category_hint(normalized(item['name']), normalized(' '.join(item.get('groups') or [item['group']])))
            previous = self.family_categories.get(item['key'])
            if previous and previous[1] >= priority:
                category, priority = previous
            elif item['id'] not in self.by_id:
                # All source/quality variants stay in one category. A named
                # channel rule beats a broad source group; unknown never wins.
                for variant in self.by_family[item['key']]:
                    original = variant.get('groups') or [variant['group']]
                    old = variant['category']
                    if old != category:
                        if old not in original:
                            self.by_group[('tv',variant['country'],old)].remove(variant)
                        if category not in original:
                            self.by_group[('tv',variant['country'],category)].append(variant)
                        variant['category'] = category
                        variant['_search'] = normalized(variant['name']+' '+variant['group']+' '+category)
                self.family_categories[item['key']] = (category, priority)
            item['category'] = category
        item['_search'] = normalized(item['name'] + ' ' + item['group'] + ' ' + item.get('category',''))
        if item['id'] not in self.by_id:
            if item['kind'] != 'episode':
                self.items.append(item)
                self.by_kind[item['kind']].append(item)
                self.by_country[(item['kind'], item['country'])].append(item)
                # Keep source-group aliases for already-open/older clients.
                groups = list(item.get('groups') or [item['group']])
                if item['kind']=='tv' and item['category'] not in groups:
                    groups.append(item['category'])
                for group in groups:
                    self.by_group[(item['kind'], item['country'], group)].append(item)
                self.by_family[item['key']].append(item)
                self.kind_counts[item['kind']] += 1
                self.cache.clear()
                self.summaries.clear()
            self.by_id[item['id']] = item
        return item

    def public(self, item):
        result = {k: item[k] for k in ('id', 'name', 'group', 'kind', 'country', 'quality', 'origin') if k in item}
        if item['kind']=='tv':
            result['group'] = item['category']
        result['favorite'] = item['key'] in self.favorites
        result['plot'] = str(item.get('plot', ''))[:1000]
        if 'season' in item:
            result['season'] = item['season']
        return result

    def counts(self):
        return dict(self.kind_counts)

    def selection(self, params):
        kind = params.get('kind', 'tv')
        country, group = params.get('country', ''), params.get('group', '')
        terms = normalized(params.get('q', '')[:100]).split()
        qual, favorites = params.get('quality', 'auto'), params.get('favorites') == '1'
        language=params.get('language','')
        origin=params.get('origin','') if kind in ('tv','all') else ''
        cache_key = (kind, country, group, tuple(terms), qual, favorites, language, origin)
        with self.lock:
            if cache_key in self.cache:
                self.cache.move_to_end(cache_key)
                return self.cache[cache_key]
            if favorites:
                source = [item for key in self.favorites for item in self.by_family.get(key, ())
                          if kind == 'all' or item['kind'] == kind]
            elif kind == 'all':
                source = self.items
            elif group and (country or kind != 'tv'):
                source = self.by_group.get((kind, country, group), ())
            elif country:
                source = self.by_country.get((kind, country), ())
            else:
                source = self.by_kind.get(kind, ())
            selected = []
            for item in source:
                if item['kind'] == 'episode' or (country and item['country'] != country) or (group and group != item.get('category') and group not in (item.get('groups') or [item['group']])):
                    continue
                if language=='ptbr' and not any(re.match(r'^(PT|BR)(?:\b|/)',normalized(g)) for g in item.get('groups') or [item['group']]):
                    continue
                if favorites and item['key'] not in self.favorites:
                    continue
                if terms and not all(term in item['_search'] for term in terms):
                    continue
                if item['kind'] == 'tv' and origin and item['origin'] != origin:
                    continue
                if item['kind'] == 'tv' and qual not in ('auto', 'all') and item['quality'] != qual:
                    continue
                selected.append(item)
            if qual != 'all':
                families = {}
                for item in selected:
                    previous = families.get(item['key'])
                    if previous is None or QUALITY_RANK[item['quality']] > QUALITY_RANK[previous['quality']]:
                        families[item['key']] = item
                selected = list(families.values())
            self.cache[cache_key] = selected
            while len(self.cache) > 5:
                self.cache.popitem(last=False)
            return selected

    def directory(self, params):
        view, kind = params.get('view'), params.get('kind', 'tv')
        key = (view, kind, params.get('country', ''), params.get('quality', 'auto'), params.get('origin',''), params.get('group',''))
        with self.lock:
            if key in self.summaries:
                self.summaries.move_to_end(key)
                return self.summaries[key]
        if view == 'origins':
            # Enumerate sources before quality/family deduplication so Auto cannot
            # hide an alternative origin of the same channel.
            selected = self.selection(dict(kind='tv',country=params.get('country',''),group=params.get('group',''),quality='all')) if kind=='tv' else []
            counter = collections.Counter(i['origin'] for i in selected)
            rows = [dict(id='origin:'+k,name=ORIGINS[k],kind='origin',count=v) for k,v in sorted(counter.items(),key=lambda pair:(pair[0]=='OTHER',pair[0]))]
        elif view == 'countries':
            counter = collections.Counter(i['country'] for i in self.selection(dict(kind='tv', quality=params.get('quality','auto'))))
            rows = [{'id': 'country:' + k, 'name': COUNTRIES.get(k, k), 'kind': 'country', 'group': str(v) + ' canais', 'count': v}
                    for k, v in sorted(counter.items(), key=lambda kv: (kv[0] != 'PT', normalized(COUNTRIES.get(kv[0], kv[0]))))]
        else:
            selection = (self.selection(dict(kind=kind, country=params.get('country', ''), quality=params.get('quality','auto'), origin=params.get('origin','')))
                         if kind == 'tv' else self.by_kind.get(kind, ()))
            counter = collections.Counter(group for i in selection for group in ([i['category']] if i['kind']=='tv' else (i.get('groups') or [i['group']])))
            rows = [{'id': 'group:', 'name': 'Todos os títulos' if kind != 'tv' else 'Todos os canais', 'kind':'group','group':'','count':len(selection)}]
            ordered = (sorted(counter.items(),key=lambda pair:CATEGORIES.index(pair[0])) if kind=='tv'
                       else sorted(counter.items(), key=lambda pair: (not normalized(pair[0]).startswith(('PT','BR')), normalized(pair[0]))))
            rows += [{'id': 'group:' + g, 'name':g,'kind':'group','group':g,'count':n} for g,n in ordered]
        with self.lock:
            self.summaries[key] = rows
            while len(self.summaries) > 256:
                self.summaries.popitem(last=False)
        return rows

    def browse(self, params):
        view, kind = params.get('view', 'items'), params.get('kind', 'tv')
        offset = max(0, min(1000000, int(params.get('offset', '0'))))
        limit = max(1, min(240 if params.get('client') == 'web' else 30, int(params.get('limit', '10'))))
        if view in ('countries', 'groups', 'origins'):
            rows = self.directory(params)
        elif view in ('seasons', 'episodes'):
            identifier = params.get('series', '')
            episodes = self.episodes(identifier)
            if view == 'seasons':
                series = self.by_id.get(identifier, {})
                counts = collections.Counter(season_key(item.get('season')) for item in episodes)
                rows = [dict(id='season:'+key, kind='season', season=key, name=season_name(key),
                             group=series.get('name', ''), count=counts[key],
                             favorite=series.get('key') in self.favorites)
                        for key in sorted(counts, key=season_order)]
            else:
                episodes = [item for item in episodes if not params.get('season')
                            or season_key(item.get('season')) == season_key(params['season'])]
                episodes = sorted(episodes, key=lambda item:(season_order(item.get('season')),
                    season_order(item.get('episode_num')), item['id']))
                rows = [self.public(item) for item in episodes]
            offset = min(offset, max(0, ((len(rows)-1)//limit)*limit))
            return {'items':rows[offset:offset+limit], 'total':len(rows), 'offset':offset,
                    'episodes':self.episode_status.get(identifier,{})}
        else:
            rows = self.selection(params)
            offset = min(offset, max(0, ((len(rows)-1)//limit)*limit))
            return {'items':[self.public(i) for i in rows[offset:offset+limit]], 'total':len(rows), 'offset':offset}
        offset = min(offset, max(0, ((len(rows)-1)//limit)*limit))
        return {'items':rows[offset:offset+limit], 'total':len(rows), 'offset':offset}

    def favorite(self, identifier, enabled):
        with self.lock:
            item = self.by_id.get(str(identifier))
            if item is None:
                raise ValueError('Item missing')
            updated = set(self.favorites)
            if enabled:
                updated.add(item['key'])
            else:
                updated.discard(item['key'])
            if updated == self.favorites:
                return self.public(item)
            if self.favorites_path:
                # Never replace unreadable or unexpectedly changed saved state with memory.
                if self.read_favorites() != self.favorites:
                    raise OSError('Favorites changed on disk; reload before saving')
                history_path = self.favorites_path.with_suffix('.history.json')
                try:
                    history = json.loads(history_path.read_text(encoding='utf-8'))
                    if not isinstance(history, list):
                        raise ValueError('Invalid history')
                except FileNotFoundError:
                    history = []
                except ValueError as error:
                    raise OSError('Invalid favorites history; preserved for recovery') from error
                history = history[-31:] + [dict(time=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    id=str(identifier), enabled=bool(enabled), before=sorted(self.favorites), after=sorted(updated))]
                atomic_batch({self.favorites_path: json_bytes(sorted(updated)),
                    self.favorites_path.with_suffix('.backup.json'): json_bytes(sorted(self.favorites)),
                    history_path: json_bytes(history)}, self.favorites_path.with_suffix('.journal.json'))
            self.favorites = updated
            self.cache.clear()
            return self.public(item)

    def episodes(self, identifier):
        series = self.by_id.get(identifier)
        if not series or series['kind'] != 'series' or not self.provider:
            return []
        with self.lock:
            if identifier in self.series_cache and time.time()-self.series_checked.get(identifier,0)<900:
                return self.series_cache[identifier]
        if self.episode_loader:
            rows, status, added = self.episode_loader(self,series)
            with self.lock:
                result = []
                for row in rows:
                    self.by_id.pop(row['id'],None)
                    result.append(self.add(row))
                if len(self.series_cache)>=64:
                    oldest = next(iter(self.series_cache))
                    self.series_cache.pop(oldest,None)
                    self.series_checked.pop(oldest,None)
                self.series_cache[identifier] = result
                self.series_checked[identifier] = time.time() if status=='ok' else time.time()-840
                self.episode_status[identifier] = dict(status=status,added=added)
                return result
        info = self.provider.fetch('get_series_info', series_id=series['provider_id'])
        result = []
        for season, episodes in sorted(info.get('episodes', {}).items(), key=lambda kv:int(kv[0]) if str(kv[0]).isdigit() else 999):
            for episode in episodes if isinstance(episodes, list) else []:
                pid = str(episode.get('id',''))
                if not pid.isdigit():
                    continue
                actual_season = str(episode.get('season') if episode.get('season') is not None else season)
                item = {'id':'e'+pid, 'provider_id':pid, 'kind':'episode', 'name':'T%s E%s · %s' % (actual_season, episode.get('episode_num',''), episode.get('title','Episódio')),
                    'group':series['name'], 'series_id':identifier, 'season':actual_season, 'episode_num':str(episode.get('episode_num','')), 'extension':str(episode.get('container_extension') or 'mp4')[:8],
                    'plot':str((episode.get('info') or {}).get('plot',''))[:1000]}
                with self.lock:
                    result.append(self.add(item))
        with self.lock:
            if len(self.series_cache) >= 64:
                oldest = next(iter(self.series_cache))
                for episode in self.series_cache.pop(oldest):
                    self.by_id.pop(episode['id'], None)
            self.series_cache[identifier] = result
            self.series_checked[identifier] = time.time()
            self.cache.clear()
        return result

    def play_url(self, identifier):
        item = self.by_id.get(str(identifier))
        if not item or item['kind'] == 'series':
            raise ValueError('Item not playable')
        if item.get('url'):
            return item['url']
        if not self.provider:
            raise ValueError('Provider unavailable')
        return self.provider.media_url('movie' if item['kind']=='movie' else 'series', item['provider_id'], item['extension'])

    def epg(self, identifier):
        item = self.by_id.get(str(identifier))
        if not item or item['kind'] != 'tv' or not self.provider or not item.get('provider_id','').isdigit():
            return {'programs':[], 'status':'unavailable'}
        with self.lock:
            cached = self.epg_cache.get(item['key'])
            if cached and time.time()-cached[0] < 300:
                return cached[1]
        try:
            variants = [c for c in self.by_family.get(item['key'], ()) if c.get('provider_id','').isdigit()]
            variants.sort(key=lambda c:(not bool(c.get('epg_id')), c['id']!=str(identifier)))
            response = {}
            deadline = time.monotonic()+7
            # The same station's SD/HD sources can have different EPG coverage.
            # Prefer an explicitly mapped source; never open its media stream.
            for variant in variants[:3]:
                if time.monotonic() >= deadline:
                    break
                try:
                    response = self.provider.fetch('get_short_epg', stream_id=variant['provider_id'], limit=4, timeout=3)
                    if response.get('epg_listings'):
                        break
                except Exception:
                    continue
            programs = []
            for entry in response.get('epg_listings', [])[:4]:
                programs.append({'title':decode_epg(entry.get('title')),'description':decode_epg(entry.get('description')),
                    'start':str(entry.get('start',''))[:25], 'end':str(entry.get('end',''))[:25],
                    'start_timestamp':str(entry.get('start_timestamp',''))[:16], 'stop_timestamp':str(entry.get('stop_timestamp',''))[:16]})
            result = {'programs':programs,'status':'ok' if programs else 'empty'}
        except Exception:
            result = {'programs':[], 'status':'unavailable'}
        with self.lock:
            if len(self.epg_cache) >= 200:
                self.epg_cache.pop(next(iter(self.epg_cache)))
            self.epg_cache[item['key']] = (time.time(), result)
        return result
