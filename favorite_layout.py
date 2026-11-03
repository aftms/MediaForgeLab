"""Private, revisioned organization of the existing household favorites."""
import copy
import json
from pathlib import Path
import threading
import uuid
from storage import atomic_batch, json_bytes, recover

KINDS = ('tv', 'movie', 'series')


class LayoutError(ValueError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


class FavoriteLayout:
    def __init__(self, path):
        self.path = Path(path)
        self.journal = self.path.with_suffix('.journal.json')
        self.lock = threading.RLock()

    def read(self):
        recover(self.journal)
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
        except FileNotFoundError:
            return dict(schema=1, revision=0, folders=[], placements={}, order={k:[] for k in KINDS})
        except (ValueError, OSError):
            raise OSError('Saved favorite organization could not be read') from None
        try:
            assert data['schema'] == 1 and type(data['revision']) is int and data['revision'] >= 0
            assert isinstance(data['folders'],list) and len(data['folders']) <= 200
            ids=set()
            for folder in data['folders']:
                assert folder['kind'] in KINDS and isinstance(folder['name'],str) and 0<len(folder['name'])<=60
                assert isinstance(folder['id'],str) and len(folder['id'])==32 and folder['id'] not in ids
                ids.add(folder['id'])
            assert isinstance(data['placements'],dict) and len(data['placements'])<=50000
            assert all(isinstance(k,str) and 0<len(k)<=200 and v in ids for k,v in data['placements'].items())
            for kind in KINDS:
                order=data['order'][kind]
                assert isinstance(order,list) and len(order)<=50000
                assert all(isinstance(k,str) and 0<len(k)<=200 for k in order)
                assert len(set(order))==len(order)
        except (AssertionError, KeyError, TypeError):
            raise OSError('Invalid saved favorite organization; original preserved') from None
        return data

    def _kind(self, kind):
        if kind not in KINDS:
            raise LayoutError('Escolha Canais, Filmes ou Séries.')
        return kind

    def _folder(self, data, kind, identifier):
        if identifier in ('', 'ungrouped'):
            return None
        folder=next((f for f in data['folders'] if f['id']==identifier and f['kind']==kind),None)
        if not folder:
            raise LayoutError('Esta pasta já não existe. Atualize os favoritos.',409)
        return folder

    def _ordered(self, catalog, data, kind, folder=''):
        self._folder(data,kind,folder)
        rows=list(catalog.selection(dict(kind=kind,favorites='1',quality='auto')))
        rank={key:i for i,key in enumerate(data['order'][kind])}
        rows.sort(key=lambda item:(rank.get(item['key'],len(rank)),item['_search'],item['id']))
        if folder:
            rows=[i for i in rows if data['placements'].get(i['key'],'ungrouped')==folder]
        return rows

    def browse(self, catalog, params):
        kind=self._kind(params.get('kind','tv'))
        with self.lock:
            data=self.read()
            all_rows=self._ordered(catalog,data,kind)
            folders=[]
            for folder in data['folders']:
                if folder['kind']==kind:
                    folders.append(dict(folder,count=sum(data['placements'].get(i['key'])==folder['id'] for i in all_rows)))
            folder=params.get('folder','')
            ordered=self._ordered(catalog,data,kind,folder)
            allowed={i['id'] for i in catalog.selection(dict(params,kind=kind,favorites='1'))}
            # Use selected quality while keeping ordering attached to channel family.
            selected=list(catalog.selection(dict(params,kind=kind,favorites='1')))
            rank={i['key']:index for index,i in enumerate(ordered)}
            selected=[i for i in selected if i['key'] in rank and i['id'] in allowed]
            selected.sort(key=lambda i:(rank[i['key']],i['id']))
            limit=max(1,min(240,int(params.get('limit',60))))
            offset=max(0,min(int(params.get('offset',0)),max(0,((len(selected)-1)//limit)*limit)))
            return dict(revision=data['revision'],folders=folders,all_count=len(all_rows),
                ungrouped_count=sum(i['key'] not in data['placements'] for i in all_rows),
                total=len(selected),offset=offset,items=[dict(catalog.public(i),
                    favorite_folder=data['placements'].get(i['key'],''),favorite_position=rank[i['key']]+1,
                    favorite_total=len(ordered)) for i in selected[offset:offset+limit]])

    def update(self, catalog, request):
        kind=self._kind(request.get('kind'))
        with self.lock:
            original=self.read()
            if type(request.get('revision')) is not int or request['revision']!=original['revision']:
                raise LayoutError('A organização mudou noutro dispositivo. A lista foi atualizada; repita a alteração.',409)
            data=copy.deepcopy(original)
            operation=request.get('operation')
            folder_id=str(request.get('folder',''))
            folder=self._folder(data,kind,folder_id)
            result={}
            if operation in ('create','rename'):
                name=' '.join(str(request.get('name','')).split())
                if not 1<=len(name)<=60:
                    raise LayoutError('O nome da pasta deve ter entre 1 e 60 caracteres.')
                if any(f['kind']==kind and f['name'].casefold()==name.casefold() and (operation=='create' or f['id']!=folder_id) for f in data['folders']):
                    raise LayoutError('Já existe uma pasta com esse nome.')
                if operation=='create':
                    if len(data['folders'])>=200:raise LayoutError('Limite de 200 pastas atingido.')
                    folder_id=uuid.uuid4().hex
                    data['folders'].append(dict(id=folder_id,name=name,kind=kind))
                elif folder:
                    folder['name']=name
                else:raise LayoutError('Escolha a pasta a renomear.')
                result['folder']=folder_id
            elif operation=='delete':
                if not folder:raise LayoutError('Escolha uma pasta criada por si.')
                data['folders']=[f for f in data['folders'] if f['id']!=folder_id]
                data['placements']={k:v for k,v in data['placements'].items() if v!=folder_id}
            elif operation in ('assign','move'):
                item=catalog.by_id.get(str(request.get('id','')))
                if not item or item['kind']!=kind or item['key'] not in catalog.favorites:
                    raise LayoutError('Este conteúdo já não é favorito. Atualize a lista.',409)
                key=item['key']
                if operation=='assign':
                    if folder:data['placements'][key]=folder_id
                    else:data['placements'].pop(key,None)
                else:
                    ordered=[i['key'] for i in self._ordered(catalog,data,kind)]
                    scope=[i['key'] for i in self._ordered(catalog,data,kind,folder_id)]
                    if key not in scope:raise LayoutError('O favorito não está nesta pasta.',409)
                    index=scope.index(key)
                    direction=request.get('direction')
                    target={'up':max(0,index-1),'down':min(len(scope)-1,index+1),'first':0,'last':len(scope)-1}.get(direction)
                    if target is None:raise LayoutError('Movimento inválido.')
                    scope.pop(index);scope.insert(target,key)
                    # Reorder only this folder's slots. Other folders retain their order.
                    keys=set(scope);values=iter(scope)
                    ordered=[next(values) if k in keys else k for k in ordered]
                    data['order'][kind]=ordered+[k for k in data['order'][kind] if k not in set(ordered)]
            else:raise LayoutError('Operação de organização inválida.')
            data['revision']+=1
            atomic_batch({self.path:json_bytes(data),self.path.with_suffix('.backup.json'):json_bytes(original)},self.journal)
            return dict(result,revision=data['revision'])
