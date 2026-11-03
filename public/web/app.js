/* Modern browser UI; shares all catalog/favorite/progress/refresh APIs with MAG. */
(()=>{'use strict';
const WEB_VERSION='20';
const $=id=>document.getElementById(id),video=$('video'),owner=crypto.randomUUID?crypto.randomUUID():('web-'+Date.now()+'-'+Math.random().toString(36).slice(2));
const labels={tv:'TV em direto',movie:'Filmes',series:'Séries',favorites:'Favoritos',continue:'Continuar a ver'};
let action='',section='tv',state={kind:'tv',view:'items',quality:'auto',country:'PT',origin:'',group:'',q:'',favorites:'0',language:''},offset=0,total=0,history=[],rows=[],sequence=0,filterSeq=0,searchTimer,pollTimer,installPrompt;
let session=null,playingItem=null,hls=null,basePosition=0,duration=0,lastSaved=0,starting=false,playerGeneration=0,audioIndex=0,subtitleIndex=-1,compatibility=false,pausedPosition=null,pauseTimer=null,pauseEpoch=0;
const display={view:'cards',sizes:{cards:60,list:120}};
try{const saved=JSON.parse(localStorage.getItem('mag-web-display-v1'));if(saved&&['cards','list'].includes(saved.view))display.view=saved.view;for(const view of ['cards','list'])if([60,120,240].includes(saved?.sizes?.[view]))display.sizes[view]=saved.sizes[view];}catch{}
function pageSize(){return display.sizes[display.view];}
function saveDisplay(){try{localStorage.setItem('mag-web-display-v1',JSON.stringify(display));}catch{}}
function renderDisplay(){const list=display.view==='list';$('cards').classList.toggle('list-view',list);document.querySelectorAll('[data-layout]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.layout===display.view)));$('page-size').value=pageSize();}
function changeDisplay(view,size){display.view=view;if(size)display.sizes[view]=size;offset=Math.floor(offset/pageSize())*pageSize();saveDisplay();renderDisplay();load();}
document.querySelectorAll('[data-layout]').forEach(b=>b.onclick=()=>changeDisplay(b.dataset.layout));$('page-size').onchange=()=>changeDisplay(display.view,Number($('page-size').value));
function text(id,value){$(id).textContent=value||'';}
async function api(path,body){const r=await fetch(path,{method:body?'POST':'GET',headers:body?{'Content-Type':'application/json','X-MAG-Action':action}:{},body:body?JSON.stringify(body):undefined,cache:'no-store'});let data;try{data=await r.json();}catch{throw Error('O computador não respondeu. Verifique a ligação.');}if(!r.ok)throw Error(data.error||'Pedido não concluído.');return data;}
function message(error){text('message',error instanceof Error?error.message:error);}
function fmt(sec){sec=Math.max(0,Math.floor(sec||0));return (sec>=3600?Math.floor(sec/3600)+':':'')+String(Math.floor(sec/60)%60).padStart(2,'0')+':'+String(sec%60).padStart(2,'0');}
function query(data){return new URLSearchParams(Object.entries(data).filter(([,v])=>v!==undefined&&v!==null)).toString();}
function button(label,fn,cls){const b=document.createElement('button');b.textContent=label;b.className=cls||'';b.onclick=fn;return b;}
function icon(kind){return kind==='season'?'series':kind;}
let favoriteLayout=null,organizing=false,organizeBusy=false,folderOperation='create',folderKind='tv';
function folderView(){return section==='favorites'&&state.view==='items';}
function orderFiltered(){return !!(state.q||state.country||state.origin||state.group||state.genre||state.language||state.quality!=='auto');}
function renderFolders(){
 const visible=folderView()&&favoriteLayout;$('folder-panel').hidden=!visible;if(!visible)return;
 const picker=$('folder-picker');picker.replaceChildren(new Option('Todos os favoritos ('+favoriteLayout.all_count+')',''),new Option('Sem pasta ('+favoriteLayout.ungrouped_count+')','ungrouped'));
 for(const f of favoriteLayout.folders)picker.add(new Option(f.name+' ('+f.count+')',f.id));picker.value=state.folder||'';
 const named=favoriteLayout.folders.some(f=>f.id===state.folder);$('rename-folder').hidden=$('delete-folder').hidden=!named;
 $('organize-favorites').setAttribute('aria-pressed',String(organizing));text('organize-favorites',organizing?'✓ Concluir organização':'↕ Organizar');
 text('folder-help',organizing?(orderFiltered()?'Limpe os filtros e escolha qualidade Auto para alterar a ordem. Pode continuar a mover conteúdos entre pastas.':'Use as setas para subir, descer, colocar no início ou no fim. Escolha uma pasta em cada cartão.'):'Crie pastas para distribuir os favoritos. A organização é partilhada pelos seus dispositivos.');
}
async function organize(request,item){
 if(organizeBusy||!favoriteLayout)return;organizeBusy=true;document.querySelectorAll('#folder-panel button,.card-organizer button,.card-organizer select').forEach(e=>e.disabled=true);
 const kind=state.kind;
 try{const result=await api('/api/favorites/layout',{kind,revision:favoriteLayout.revision,...request});if(section==='favorites'&&state.kind===kind){if(request.operation==='create')state.folder=result.folder;if(request.operation==='delete')state.folder='ungrouped';
 if(request.operation==='move'&&item){const p={up:item.favorite_position-2,down:item.favorite_position,first:0,last:item.favorite_total-1}[request.direction];offset=Math.floor(Math.max(0,p)/pageSize())*pageSize();}
 organizeBusy=false;await load();if(item)document.querySelector('[data-favorite-id="'+CSS.escape(item.id)+'"] [data-move="'+request.direction+'"]')?.focus();}return true;
 }catch(e){organizeBusy=false;await load();message(e);text('folder-error',e.message);return false;}
 finally{organizeBusy=false;document.querySelectorAll('#folder-panel button').forEach(e=>e.disabled=false);}
}
function organizer(card,item){
 const controls=document.createElement('div');controls.className='card-organizer';card.dataset.favoriteId=item.id;
 const moves=document.createElement('div');moves.className='favorite-moves';
 for(const [direction,label,title] of [['first','⇤','Colocar no início'],['up','↑','Subir'],['down','↓','Descer'],['last','⇥','Colocar no fim']]){const b=button(label,()=>organize({operation:'move',id:item.id,folder:state.folder||'',direction},item));b.dataset.move=direction;b.title=title;b.setAttribute('aria-label',title+' · '+item.name);b.disabled=orderFiltered()||organizeBusy||((direction==='first'||direction==='up')?item.favorite_position===1:item.favorite_position===item.favorite_total);moves.append(b);}
 const position=document.createElement('small');position.textContent='Posição '+item.favorite_position+' de '+item.favorite_total;
 const select=document.createElement('select');select.setAttribute('aria-label','Pasta de '+item.name);select.add(new Option('Sem pasta',''));for(const f of favoriteLayout.folders)select.add(new Option(f.name,f.id));select.value=item.favorite_folder;select.disabled=organizeBusy;select.onchange=()=>organize({operation:'assign',id:item.id,folder:select.value},item);
 controls.append(position,moves,select);card.append(controls);card.classList.add('organizing');
}
function editFolder(operation){if(!favoriteLayout||organizeBusy)return;folderOperation=operation;folderKind=state.kind;const folder=favoriteLayout.folders.find(f=>f.id===state.folder);
 text('folder-title',operation==='create'?'Nova pasta':operation==='rename'?'Renomear pasta':'Apagar pasta');$('folder-name-label').hidden=operation==='delete';$('folder-name').required=operation!=='delete';$('folder-name').value=operation==='rename'?folder.name:'';
 text('folder-explanation',operation==='delete'?'Apagar «'+folder.name+'»? Os conteúdos continuam favoritos e passam para Sem pasta.':'Esta pasta pertence a '+({tv:'Canais',movie:'Filmes',series:'Séries'}[state.kind])+'.');text('folder-error','');text('folder-save',operation==='delete'?'Apagar pasta':'Guardar');$('folder-dialog').showModal();if(operation!=='delete')$('folder-name').focus();}
$('folder-picker').onchange=()=>{state.folder=$('folder-picker').value;offset=0;load();};$('new-folder').onclick=()=>editFolder('create');$('rename-folder').onclick=()=>editFolder('rename');$('delete-folder').onclick=()=>editFolder('delete');$('organize-favorites').onclick=()=>{organizing=!organizing;render();};$('folder-cancel').onclick=()=>$('folder-dialog').close();
$('folder-form').onsubmit=async event=>{event.preventDefault();if(folderKind!==state.kind)return;$('folder-save').disabled=true;try{if(await organize({operation:folderOperation,folder:folderOperation==='create'?'':state.folder,name:$('folder-name').value}))$('folder-dialog').close();}finally{$('folder-save').disabled=false;}};
function render(){
 renderDisplay();renderFolders();
 text('title',labels[section]);text('count',total.toLocaleString('pt-PT')+' títulos');text('page',total?`${Math.floor(offset/pageSize())+1} / ${Math.ceil(total/pageSize())}`:'');$('prev').disabled=offset===0;$('next').disabled=offset+pageSize()>=total;
 $('back').hidden=!history.length;$('favorite-types').hidden=section!=='favorites';
 text('breadcrumb',(state.seriesName?state.seriesName+(state.seasonName?' / '+state.seasonName:''):'')||state.group|| (section==='continue'?'Retome de onde ficou':state.kind==='tv'?(state.country==='PT'?'Canais de Portugal':'Todos os canais'):'Toda a biblioteca'));
 if(folderView())text('breadcrumb',state.folder==='ungrouped'?'Sem pasta':favoriteLayout?.folders.find(f=>f.id===state.folder)?.name||'Todos os favoritos');
 document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('active',b.dataset.section===section));
 document.querySelectorAll('[data-kind]').forEach(b=>b.classList.toggle('active',b.dataset.kind===state.kind));
 $('origin').hidden=state.kind!=='tv'||section==='continue';$('country').hidden=section==='continue'||state.view!=='items';$('genre').hidden=!['movie','series'].includes(state.kind)||section==='continue'||state.view!=='items';$('quality').hidden=state.kind!=='tv'||section==='continue';$('category').hidden=section==='continue'||state.view!=='items';$('ptbr').parentElement.hidden=section==='continue';
 $('cards').replaceChildren();
 for(const item of rows){
  const card=document.createElement('article');card.className='card';const open=button('',()=>openItem(item),'card-open');
  const art=document.createElement('div');art.className='art '+item.kind;const image=document.createElement('img');image.src='/assets/'+icon(item.kind)+'.png';image.alt='';art.append(image);
  const body=document.createElement('div');body.className='card-content';const title=document.createElement('h3');title.textContent=item.name;open.title=item.name;const detail=document.createElement('p');detail.textContent=item.count!==undefined?`${item.count} episódios`:item.progress?`${fmt(item.progress.position)} / ${fmt(item.progress.duration)}`:item.group;body.append(title,detail);open.append(art,body);card.append(open);
  const badge=document.createElement('span');badge.className='badge';badge.textContent=item.kind==='tv'?item.quality==='UNKNOWN'?'DIRETO':item.quality:item.kind==='season'?'TEMPORADA':item.kind==='episode'?'EPISÓDIO':item.kind==='movie'?'FILME':'SÉRIE';card.append(badge);
  if(item.kind!=='season'){const star=button(item.favorite?'★':'☆',async()=>{star.disabled=true;try{await favorite(item);render();}catch(e){message(e);}finally{star.disabled=false;}},'star');star.setAttribute('aria-label',item.favorite?'Remover favorito':'Guardar favorito');card.append(star);}
  if(folderView()&&organizing&&favoriteLayout)organizer(card,item);
  $('cards').append(card);
 }
 if(!rows.length)message(folderView()&&state.folder?'Esta pasta está vazia nesta seleção. Em Todos os favoritos → Organizar, escolha uma pasta para cada conteúdo.':'Nenhum título nesta seleção. Experimente outro filtro.');
}
async function load(){const serial=++sequence;message('A carregar…');try{const data=section==='continue'?await api('/api/continue'):await api((folderView()?'/api/favorites?':'/api/catalog?')+query({...state,offset,limit:pageSize(),client:'web'}));if(serial!==sequence)return;if(folderView())favoriteLayout=data;if(section==='continue'){const matches=data.items.filter(i=>!state.q||i.name.toLocaleLowerCase().includes(state.q.toLocaleLowerCase()));data.total=matches.length;data.offset=offset;data.items=matches.slice(offset,offset+pageSize());}rows=data.items;total=data.total===undefined?rows.length:data.total;offset=data.offset||0;message('');render();}catch(e){if(serial===sequence)message(e);}}
async function directories(view,extra={}){let all=[],pos=0;do{const data=await api('/api/catalog?'+query({kind:state.kind,view,country:state.country,...extra,offset:pos,limit:30}));all.push(...data.items);pos+=30;if(pos>=data.total)break;}while(pos<3000);return all;}
async function filters(){const seq=++filterSeq;const fill=(node,data,first)=>{node.replaceChildren(new Option(first,''));for(const item of data)if(item.kind==='country'||item.kind==='origin'||item.kind==='genre'||item.group)node.add(new Option(item.name,item.kind==='country'?item.id.slice(8):item.kind==='origin'?item.id.slice(7):item.kind==='genre'?item.id.slice(6):item.group));};try{const countries=await directories('countries');if(seq!==filterSeq)return;fill($('country'),countries,'Todos os países');$('country').value=state.country;if(state.kind==='tv'){const origins=await directories('origins');if(seq!==filterSeq)return;fill($('origin'),origins,'Todas as origens');$('origin').value=state.origin||'';}const groups=await directories('groups');if(seq!==filterSeq)return;fill($('category'),groups,'Todas as categorias');$('category').value=state.group||'';if(['movie','series'].includes(state.kind)){const genres=await directories('genres');if(seq!==filterSeq)return;fill($('genre'),genres,'Todos os géneros');$('genre').value=state.genre||'';}}catch(e){message(e);}}
function select(next,kind){favoriteLayout=null;organizing=false;section=next;state={kind:kind||(['favorites','continue'].includes(next)?'tv':next),view:'items',quality:$('quality').value,country:next==='tv'?'PT':'',origin:'',group:'',genre:'',q:'',folder:'',favorites:next==='favorites'?'1':'0',language:$('ptbr').checked?'ptbr':''};history=[];offset=0;$('search').value='';$('country').value=state.country;$('category').value='';load();filters();}
function openItem(item){if(['series','season'].includes(item.kind)){history.push({state:{...state},offset});state=item.kind==='series'?{...state,view:'seasons',series:item.id,seriesName:item.name,season:'',seasonName:'',q:''}:{...state,view:'episodes',season:item.season,seasonName:item.name};offset=0;load();}else play(item);}
async function favorite(item){const data=await api('/api/favorite',{id:item.id,favorite:!item.favorite});item.favorite=data.favorite;if(playingItem&&playingItem.id===item.id)text('play-favorite',data.favorite?'★ Remover favorito':'☆ Guardar favorito');if(section==='favorites')await load();}
/* The player browses a frozen filter context, one metadata page at a time. */
let playbackList=null,listGeneration=0,selectionBusy=false;
function playable(item){return ['tv','movie','episode'].includes(item.kind);}
function capturePlaybackList(item){const at=rows.findIndex(row=>row.id===item.id);playbackList=at<0?null:{section,state:{...state},items:rows.slice(),offset,total,size:pageSize(),index:offset+at,loading:false};}
function renderPlaybackList(){const list=playbackList,box=$('play-list');$('play-navigation').hidden=!list;if(!list)return;const busy=selectionBusy||starting||list.loading;
 $('play-previous').disabled=busy||list.index<=0;$('play-next').disabled=busy||list.index>=list.total-1;box.disabled=busy;
 box.replaceChildren(new Option(list.loading?'A carregar lista…':'Escolher da lista ativa…',''));
 if(list.offset>0)box.add(new Option('↑ Página anterior da lista','page:previous'));
 list.items.forEach((item,i)=>{if(playable(item))box.add(new Option((list.offset+i+1)+'. '+item.name,String(i)));});
 if(list.offset+list.items.length<list.total)box.add(new Option('↓ Página seguinte da lista','page:next'));
 const selected=list.items.findIndex(item=>item.id===playingItem?.id);box.value=selected<0?'':String(selected);
 text('play-list-position',(list.index+1)+' / '+list.total);
}
async function fetchPlaybackPage(wanted){const list=playbackList,stamp=listGeneration;if(!list||list.loading)return false;list.loading=true;renderPlaybackList();try{
 let data;if(list.section==='continue'){data=await api('/api/continue');const matches=data.items.filter(i=>!list.state.q||i.name.toLocaleLowerCase().includes(list.state.q.toLocaleLowerCase()));data={items:matches.slice(wanted,wanted+list.size),offset:wanted,total:matches.length};}
 else data=await api((list.section==='favorites'&&list.state.view==='items'?'/api/favorites?':'/api/catalog?')+query({...list.state,offset:wanted,limit:list.size,client:'web'}));
 if(stamp!==listGeneration||playbackList!==list)return false;list.items=data.items;list.offset=data.offset||0;list.total=data.total===undefined?data.items.length:data.total;return true;
 }catch(e){if(stamp===listGeneration)text('play-status','Não foi possível carregar a lista. '+e.message);return false;}finally{list.loading=false;if(playbackList===list)renderPlaybackList();}}
async function adjacentPlayback(delta){const list=playbackList;if(!list||selectionBusy||starting||list.loading)return;const target=list.index+delta;if(target<0||target>=list.total)return;
 if(target<list.offset||target>=list.offset+list.items.length){if(!await fetchPlaybackPage(Math.floor(target/list.size)*list.size))return;}
 if(playbackList!==list)return;const item=list.items[target-list.offset];if(item&&playable(item)){list.index=target;await play(item,undefined,true);}}
async function choosePlayback(){const list=playbackList,value=$('play-list').value;if(!list||selectionBusy||starting||list.loading||value==='')return;
 if(value==='page:previous'||value==='page:next'){await fetchPlaybackPage(Math.max(0,list.offset+(value==='page:next'?list.size:-list.size)));return;}
 const index=Number(value),item=list.items[index];if(!item||!playable(item)||item.id===playingItem?.id)return;list.index=list.offset+index;await play(item,undefined,true);}
function closePlaybackList(){++listGeneration;playbackList=null;renderPlaybackList();}
$('play-previous').onclick=()=>adjacentPlayback(-1);$('play-next').onclick=()=>adjacentPlayback(1);$('play-list').onchange=choosePlayback;
const trackControls=new MediaTrackControls($('media-tracks'),video,()=>video.currentTime||0,(audio,subtitle)=>{audioIndex=audio;subtitleIndex=subtitle;if(pausedPosition===null)seekOrRestart();},$('player'));
function updateTime(){if(starting||!session)return;const now=basePosition+(video.currentTime||0);text('play-time',fmt(now)+' / '+(duration>0?fmt(duration):'—'));if(document.activeElement!==$('timeline'))$('timeline').value=now;if(now-lastSaved>=15||now<lastSaved-20){lastSaved=now;saveProgress();}}
function cancelPauseRelease(){clearTimeout(pauseTimer);pauseTimer=null;++pauseEpoch;}
function schedulePauseRelease(){
 cancelPauseRelease();if(starting||!session||video.ended||!video.paused)return;
 const epoch=pauseEpoch,serial=playerGeneration,current=session;
 pauseTimer=setTimeout(async()=>{
  if(epoch!==pauseEpoch||serial!==playerGeneration||session!==current||!video.paused||starting||video.ended)return;
  await saveProgress();
  if(epoch!==pauseEpoch||serial!==playerGeneration||session!==current||!video.paused||starting)return;
  pausedPosition=basePosition+(video.currentTime||0);session=null;clearTimeout(pollTimer);
  if(hls)hls.stopLoad();text('play-status','Em pausa · ligação libertada. Prima ▶ para retomar.');
  try{await api('/api/media/stop',{token:current.token});}catch{}
 },900);
}
async function saveProgress(){if(starting||!session||!playingItem||playingItem.kind==='tv')return;const position=Math.max(0,Math.floor(basePosition+(video.currentTime||0)));try{await api('/api/progress',{id:playingItem.id,position,duration:Math.floor(duration),completed:duration>0&&position>=duration-8});}catch{/* Keep playback running if saving fails. */}}
function detach(){cancelPauseRelease();trackControls.prepare();video.pause();if(hls){hls.destroy();hls=null;}video.removeAttribute('src');video.load();}
async function stop(){cancelPauseRelease();if(document.pictureInPictureElement===video){try{await document.exitPictureInPicture();}catch{}}pausedPosition=null;++playerGeneration;clearTimeout(pollTimer);await saveProgress();detach();const previous=session;session=null;starting=false;trackControls.reset();if(previous){try{await api('/api/media/stop',{token:previous.token});}catch{}}}
async function play(item,position,keepList=false){if(starting||selectionBusy)return;selectionBusy=true;const stamp=++listGeneration;if(!keepList)capturePlaybackList(item);renderPlaybackList();try{await stop();if(stamp!==listGeneration)return;playingItem=item;compatibility=false;audioIndex=item.kind==='tv'?0:'auto';subtitleIndex=-1;trackControls.reset();if(!$('player').open)$('player').showModal();text('play-title',item.name);text('play-kind',item.kind==='tv'?'EM DIRETO':item.kind==='episode'?'EPISÓDIO':'FILME');text('plot',item.plot);text('play-favorite',item.favorite?'★ Remover favorito':'☆ Guardar favorito');$('vod-seek').hidden=item.kind==='tv';$('rewind').hidden=$('forward').hidden=item.kind==='tv';await start(position);}finally{selectionBusy=false;renderPlaybackList();}}

let hlsLoader=null;
async function ensureHls(){
 if(typeof Hls!=='undefined'||video.canPlayType('application/vnd.apple.mpegurl'))return;
 if(!hlsLoader)hlsLoader=new Promise((resolve,reject)=>{
  const script=document.createElement('script');let timer;
  const done=error=>{clearTimeout(timer);script.onload=script.onerror=null;script.remove();error?reject(error):resolve();};
  script.src='/web/vendor/hls.min.js';
  script.onload=()=>done(typeof Hls==='undefined'?Error('O leitor não carregou. Feche e tente novamente.'):null);
  script.onerror=()=>done(Error('Não foi possível carregar o leitor. Feche e tente novamente.'));
  timer=setTimeout(()=>done(Error('O carregamento do leitor demorou demasiado. Feche e tente novamente.')),15000);
  document.head.append(script);
 }).finally(()=>{hlsLoader=null;});
 await hlsLoader;
}
function preparing(data){
 renderPlaybackList();
 const known=Number.isFinite(data?.duration)&&data.duration>0;
 duration=known?data.duration:0;
 $('timeline').disabled=true;$('timeline').max=Math.max(1,duration);$('timeline').value=known?basePosition:0;
 text('play-time',fmt(basePosition)+' / '+(known?fmt(duration):'—'));
 for(const id of ['rewind','forward','compatible'])$(id).disabled=true;
 const stages={analysis:'A verificar o formato e o áudio…',remux:'A preparar os primeiros segundos…',transcode:'A adaptar o vídeo para o navegador…'};
 text('play-status',stages[data?.stage]||'A ligar ao conteúdo…');
}
async function start(position){pausedPosition=null;starting=true;const serial=++playerGeneration;detach();basePosition=Math.max(0,position||0);preparing();try{await ensureHls();if(serial!==playerGeneration)return;const data=await api('/api/media/web',{owner,id:playingItem.id,...(position!==undefined?{position}:{}),audio:audioIndex,subtitle:subtitleIndex,compatibility});if(serial!==playerGeneration){await api('/api/media/stop',{token:data.token});return;}session=data;basePosition=data.position;lastSaved=basePosition;preparing(data);await ready(serial);}catch(e){if(serial!==playerGeneration)return;starting=false;renderPlaybackList();$('compatible').disabled=false;text('play-status',e.message);}}
async function ready(serial){if(serial!==playerGeneration||!session)return;try{const data=await api('/api/media/pulse',{token:session.token});if(serial!==playerGeneration)return;if(data.state!=='ready'){preparing(data);pollTimer=setTimeout(()=>ready(serial),700);return;}session=data;duration=data.duration;$('timeline').disabled=!(duration>0);for(const id of ['rewind','forward'])$(id).disabled=!(duration>0);$('compatible').disabled=false;$('timeline').max=Math.max(1,duration);$('timeline').value=basePosition;trackControls.update(data);audioIndex=data.audio_index||0;subtitleIndex=data.subtitle_index===undefined?-1:data.subtitle_index;
 text('play-status',data.video_mode==='remux'?'Vídeo original · formato adaptado para o navegador':'Vídeo adaptado para compatibilidade');
 if(typeof Hls!=='undefined'&&Hls.isSupported()){hls=new Hls({enableWorker:true,backBufferLength:12,maxBufferLength:20,maxMaxBufferLength:30,startPosition:0,liveSyncDurationCount:1});hls.loadSource(data.url);hls.attachMedia(video);hls.on(Hls.Events.MANIFEST_PARSED,()=>video.play().catch(()=>text('play-status','Prima ▶ para reproduzir.')));hls.on(Hls.Events.ERROR,(_,e)=>{if(e.fatal)text('play-status','Não foi possível reproduzir. Experimente o modo compatível ou feche e volte a abrir.');});}
 else if(video.canPlayType('application/vnd.apple.mpegurl')){video.src=data.url;video.play().catch(()=>{});}else throw Error('Este navegador não suporta o leitor. Use Chrome ou Edge atualizado.');
 starting=false;renderPlaybackList();pulse();
 }catch(e){if(serial!==playerGeneration)return;starting=false;renderPlaybackList();$('compatible').disabled=false;text('play-status','Não foi possível preparar o vídeo. '+e.message);}}
function pulse(){clearTimeout(pollTimer);pollTimer=setTimeout(async()=>{if(!session)return;const current=session;try{const data=await api('/api/media/pulse',{token:current.token});if(session!==current)return;trackControls.feed(data);pulse();}catch(e){if(session!==current)return;detach();session=null;text('play-status',e.message);}},subtitleIndex>=0?1000:20000);}
async function seek(position){if(!session||starting||playingItem.kind==='tv')return;await saveProgress();clearTimeout(pollTimer);await start(Math.min(Math.max(0,position),Math.max(0,duration-1)));}
async function refreshStatus(){try{const s=await api('/api/refresh');$('refresh').disabled=s.running;text('refresh',s.running?'A verificar…':'↻ Atualizar catálogo');const a=s.summary&&s.summary.added;const when=s.last_success?new Date(s.last_success).toLocaleString('pt-PT'):'ainda não realizada';text('refresh-status',(s.error||s.running&&s.stage||a&&`${a.tv} canais, ${a.movie} filmes e ${a.series} séries adicionados`||'')+' · Última atualização: '+when);if(s.running)setTimeout(refreshStatus,2500);}catch(e){text('refresh-status',e.message);}}
document.querySelectorAll('[data-section]').forEach(b=>b.onclick=()=>select(b.dataset.section));document.querySelectorAll('[data-kind]').forEach(b=>b.onclick=()=>select('favorites',b.dataset.kind));
$('search').oninput=()=>{clearTimeout(searchTimer);searchTimer=setTimeout(()=>{state={...state,view:'items',series:'',seriesName:'',season:'',seasonName:'',q:$('search').value};offset=0;history=[];load();},280);};
$('country').onchange=()=>{state.country=$('country').value;state.group='';state.genre='';state.origin='';offset=0;load();filters();};$('origin').onchange=()=>{state.origin=$('origin').value;offset=0;load();};$('genre').onchange=()=>{state.genre=$('genre').value;offset=0;load();};$('category').onchange=()=>{state.group=$('category').value;offset=0;load();};$('quality').onchange=()=>{state.quality=$('quality').value;offset=0;load();};$('ptbr').onchange=()=>{state.language=$('ptbr').checked?'ptbr':'';offset=0;load();};
$('back').onclick=()=>{const saved=history.pop();if(saved){state=saved.state;offset=Math.floor(saved.offset/pageSize())*pageSize();load();}};async function turnPage(direction){offset=Math.max(0,offset+direction*pageSize());await load();document.querySelector('.list-heading').scrollIntoView({block:'start'});}
$('prev').onclick=()=>turnPage(-1);$('next').onclick=()=>turnPage(1);
$('refresh').onclick=async()=>{try{await api('/api/refresh',{});refreshStatus();}catch(e){message(e);}};
/* Native PiP keeps the same media element and household playback lease. */
function updatePipButton(){const supported=!!document.pictureInPictureEnabled&&typeof video.requestPictureInPicture==='function',active=document.pictureInPictureElement===video;const button=$('player-pip');button.hidden=!supported;button.disabled=!supported||(!active&&(video.readyState<2||!video.videoWidth));button.setAttribute('aria-pressed',String(active));button.setAttribute('aria-label',active?'Repor vídeo na página':'Destacar vídeo sempre à frente');button.title=active?'Repor vídeo na página':'Destacar vídeo sempre à frente';text('player-pip-label',active?'Repor':'Destacar');}
$('player-pip').onclick=async()=>{const serial=playerGeneration;$('player-pip').disabled=true;try{if(document.pictureInPictureElement===video)await document.exitPictureInPicture();else{if(document.fullscreenElement)await document.exitFullscreen();await video.requestPictureInPicture();if(serial!==playerGeneration&&document.pictureInPictureElement===video)await document.exitPictureInPicture();}}catch{if(serial===playerGeneration)text('play-status','Não foi possível destacar o vídeo. Tente novamente depois de começar a reprodução.');}finally{updatePipButton();}};
for(const event of ['loadeddata','emptied','enterpictureinpicture','leavepictureinpicture'])video.addEventListener(event,updatePipButton);
updatePipButton();
/* Window sizing changes presentation only; the same video/HLS session continues. */
let lastFullscreenChange=0;
function resizePlayer(delta){const box=$('player');if(document.fullscreenElement)return;const max=innerWidth*.96,min=Math.min(420,max);box.style.width=Math.max(min,Math.min(max,box.getBoundingClientRect().width+delta))+'px';box.style.height='auto';}
$('player-smaller').onclick=()=>resizePlayer(-160);$('player-larger').onclick=()=>resizePlayer(160);
async function setFullscreen(enabled){if(!!document.fullscreenElement===enabled)return;try{if(enabled)await video.requestFullscreen();else await document.exitFullscreen();}catch{setTimeout(()=>{if(!!document.fullscreenElement!==enabled)text('play-status','Use o botão de ecrã inteiro nos controlos do vídeo.');},100);}}
function toggleFullscreen(){return setFullscreen(!document.fullscreenElement);}
$('player-fullscreen').onclick=toggleFullscreen;
let surfaceClick=null;
video.addEventListener('mousedown',event=>{if(event.button===0&&event.detail===1)surfaceClick={time:Date.now(),playing:!video.paused,fullscreen:!!document.fullscreenElement,generation:playerGeneration};});
video.addEventListener('dblclick',event=>{
 // Leave the native control strip (volume, timeline, etc.) to the browser.
 const bounds=video.getBoundingClientRect();if(event.button!==0||event.clientY>bounds.bottom-80)return;
 event.preventDefault();event.stopPropagation();
 const resume=surfaceClick&&Date.now()-surfaceClick.time<800&&surfaceClick.playing&&surfaceClick.generation===playerGeneration;
 cancelPauseRelease();setFullscreen(surfaceClick?!surfaceClick.fullscreen:!document.fullscreenElement);
 if(resume&&video.paused&&session&&!starting)video.play().catch(()=>{});
 else if(video.paused&&session&&!starting)schedulePauseRelease();
 surfaceClick=null;
},true);
document.addEventListener('fullscreenchange',()=>{lastFullscreenChange=Date.now();if(video.paused&&session&&!starting)schedulePauseRelease();});
window.addEventListener('resize',()=>{if(video.paused&&session&&!starting)schedulePauseRelease();});
$('close-player').onclick=async()=>{closePlaybackList();await stop();$('player').close();};$('player').addEventListener('cancel',event=>{if(document.fullscreenElement||Date.now()-lastFullscreenChange<500){event.preventDefault();return;}closePlaybackList();stop();});video.ontimeupdate=updateTime;
video.onpause=schedulePauseRelease;
video.onplay=()=>{cancelPauseRelease();if(pausedPosition!==null&&!starting){const position=playingItem.kind==='tv'?0:pausedPosition;start(position);}};
video.onended=()=>{saveProgress();text('play-status','Reprodução terminada.');stop();};
$('timeline').onchange=()=>seek(Number($('timeline').value));$('rewind').onclick=()=>seek(basePosition+video.currentTime-30);$('forward').onclick=()=>seek(basePosition+video.currentTime+30);$('compatible').onclick=()=>{compatibility=true;seekOrRestart();};function seekOrRestart(){if(!starting&&playingItem&&pausedPosition===null){clearTimeout(pollTimer);start(playingItem.kind==='tv'?0:basePosition+video.currentTime);}}
$('play-favorite').onclick=async()=>{try{await favorite(playingItem);render();}catch(e){text('play-status',e.message);}};
$('settings').onclick=async()=>{$('source-url').value='';text('source-status','');$('settings-panel').showModal();try{const s=await api('/api/source');text('source-server',s.server?'Servidor: '+s.server:'Origem ainda não configurada.');}catch(e){text('source-status',e.message);}};$('close-settings').onclick=()=>{$('source-url').value='';$('settings-panel').close();};$('settings-panel').addEventListener('close',()=>{$('source-url').value='';});$('save-source').onclick=async()=>{try{await api('/api/source',{url:$('source-url').value});$('source-url').value='';text('source-status','Origem guardada. Atualize o catálogo para a aplicar.');}catch(e){text('source-status',e.message);}};
/* Installation stays discoverable even without a browser-provided prompt. */
const installDisplay=window.matchMedia('(display-mode: standalone)');
let appInstalled=installDisplay.matches||navigator.standalone===true;
function installLabel(){text('install-label',appInstalled?'Aplicação instalada':'Instalar aplicação');$('install').hidden=false;}
function installHelp(detail){text('install-status',detail||(appInstalled?'A Media Forge Lab já está aberta como aplicação.':!window.isSecureContext?'Este endereço HTTP da rede local não permite instalar a aplicação. Abra um dos endereços abaixo.':'A instalação direta ainda não está disponível nesta janela. Siga os passos do seu navegador abaixo.'));const ua=navigator.userAgent||'',guide=/Android/i.test(ua)?'android':/Edg\//.test(ua)?'edge':'chrome';for(const name of ['chrome','edge','android'])$('install-'+name).open=name===guide;$('install-instructions').hidden=appInstalled;$('install-address-help').hidden=window.isSecureContext;$('install-panel').showModal();}
window.addEventListener('beforeinstallprompt',event=>{event.preventDefault();installPrompt=event;installLabel();});
window.addEventListener('appinstalled',()=>{installPrompt=null;appInstalled=true;installLabel();if($('install-panel').open)installHelp('Aplicação instalada. Pode abri-la na lista de aplicações do dispositivo.');});
if(installDisplay.addEventListener)installDisplay.addEventListener('change',event=>{appInstalled=event.matches||navigator.standalone===true;installLabel();});
$('install').onclick=async()=>{if(appInstalled||!installPrompt){installHelp();return;}const prompt=installPrompt;installPrompt=null;$('install').disabled=true;try{await prompt.prompt();const choice=await prompt.userChoice;if(choice.outcome==='dismissed')installHelp('A instalação foi cancelada. Pode voltar a tentar pelo menu do navegador.');}catch{installHelp('Não foi possível abrir a instalação direta. Use a opção de instalação do navegador.');}finally{$('install').disabled=false;installLabel();}};
$('close-install').onclick=()=>$('install-panel').close();installLabel();
/* The displayed version belongs to the interface actually loaded. */
text('web-version','Web v'+WEB_VERSION);
text('about-version','v'+WEB_VERSION);
$('about').onclick=()=>{text('about-mode',installDisplay.matches||navigator.standalone===true?'Aplicação instalada (PWA)':'Navegador');$('about-panel').showModal();};
$('close-about').onclick=()=>$('about-panel').close();
/* End installation controls. */
window.addEventListener('pagehide',()=>{if(session){fetch('/api/media/stop',{method:'POST',headers:{'Content-Type':'application/json','X-MAG-Action':action},body:JSON.stringify({token:session.token}),keepalive:true}).catch(()=>{});}});
async function connection(){try{const s=await api('/api/media/status');text('connection',s.active?'● Em reprodução: '+s.device:'● Pronto · uma ligação disponível');}catch{text('connection','Sem ligação ao computador');}setTimeout(connection,10000);}
(async()=>{try{const data=await api('/api/library');action=data.action_token;text('summary',`${(data.counts.tv||0).toLocaleString('pt-PT')} canais · ${(data.counts.movie||0).toLocaleString('pt-PT')} filmes · ${(data.counts.series||0).toLocaleString('pt-PT')} séries`);await load();filters();refreshStatus();connection();if('serviceWorker'in navigator&&window.isSecureContext)navigator.serviceWorker.register('/web/sw.js',{scope:'/web/'}).catch(()=>{});}catch(e){message(e);}})();
})();
