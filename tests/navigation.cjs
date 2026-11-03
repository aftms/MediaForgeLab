/* Executes production ES5 UI with a tiny DOM, fake HTTP and native player.
   No browser, real provider URL, account credentials or IPTV streams. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../public/portal.js'),'utf8');
const html=fs.readFileSync(path.join(__dirname,'../public/index.html'),'utf8');
const boot=fs.readFileSync(path.join(__dirname,'../public/boot.js'),'utf8');
const mediaTracks=fs.readFileSync(path.join(__dirname,'../public/media-tracks.js'),'utf8');
function harness(native=true, opts={}) {
  class Element {
    constructor(tag){this.tag=tag;this.children=[];this.style={};this.className='';}
    get firstChild(){return this.children[0];}
    appendChild(node){this.children.push(node);}
    removeChild(node){this.children.splice(this.children.indexOf(node),1);}
    focus(){}
    getElementsByTagName(tag){return this.children.filter(c=>c.tag===tag);}
    get value(){return this.children.map(c=>c.value||'').join('');}
    set value(value){this.children=[{value}];}
  }
  const nodes={},timers=new Map(),calls=[],requests=[],pending=[],favorites=opts.favorites||new Set(),storage=opts.storage||{};let timer=0,clock=100000,position=120;
  for(const match of html.matchAll(/id="([^"]+)"/g))nodes[match[1]]=new Element('div');
  const tv=Array.from({length:12},(_,i)=>({id:String(i+1),name:'Canal '+(i+1)+' FHD',kind:'tv',country:'PT',group:'PT| TV',quality:'FHD'}));
  const films=[{id:'m10',name:'Câmara de Cinema',kind:'movie',country:'',group:'PT/BR',quality:'HD',plot:'Um filme.'}];
  const series=[{id:'s20',name:'Uma série',kind:'series',group:'PT',country:'',quality:'UNKNOWN'}];
  const episodes=opts.episodes||[{season:'1',id:'e201',name:'T1 E1 · Início',kind:'episode',group:'Uma série',quality:'HD'}];
  const all=tv.concat(films,series);
  function respond(url,body) {
    if(url==='/api/refresh')return body?{running:true,stage:'A verificar filmes'}:opts.refreshStatus||{running:false,last_success:'2026-11-02T20:00:00Z',summary:{added:{tv:12,movie:35,series:4}}};
    if(url==='/api/source')return {configured:true,server:'http://fixture.invalid'};
    if(url==='/api/progress')return {saved:true};
    if(url==='/api/player-diagnostics')return opts.failDiagnostics?null:{saved:true};
    if(url==='/api/library')return {counts:{tv:12,movie:1,series:1},action_token:'fixture-action',switch_delay_ms:1000,player_solution:'ffmpeg'};
    if(url==='/api/favorite'){if(opts.failFavorite)return null;const item=all.concat(episodes).find(i=>i.id===body.id),id=item.kind==='episode'?'s20':body.id;if(body.favorite)favorites.add(id);else favorites.delete(id);return {...item,favorite:body.favorite};}
    if(url==='/api/media/stop')return {stopped:true};
    if(url==='/api/media/pulse')return {state:'ready'};
    if(url==='/api/media/mag')return {token:'fixture-media-token',url:'http://fixture.invalid/media.ts',progress:{position:opts.resume||0}};
    if(url.startsWith('/api/epg/'))return {status:'ok',programs:[{title:'Programa real',start:'2026-11-02 18:00:00',end:'2026-11-02 19:00:00'}]};
    if(url.startsWith('/api/catalog?')) {
      const p=new URL('http://fixture.invalid'+url).searchParams;let rows;
      if(p.get('view')==='countries')rows=[{id:'country:PT',name:'Portugal',kind:'country',group:'12 canais',count:12}];
      else if(p.get('view')==='genres')rows=[{id:'genre:Drama',name:'Drama',kind:'genre',count:1}];
      else if(p.get('view')==='origins')rows=[{id:'origin:MEO',name:'MEO',kind:'origin',count:6},{id:'origin:VO',name:'VO · Vodafone',kind:'origin',count:6}];
      else if(p.get('view')==='groups')rows=opts.groups||[{id:'group:',name:'Todos os títulos',kind:'group',group:'',count:12}];
      else if(p.get('view')==='seasons')rows=Array.from(new Set(episodes.map(e=>e.season))).map(season=>({id:'season:'+season,season,kind:'season',name:'Temporada '+season,group:'Uma série',count:episodes.filter(e=>e.season===season).length}));
      else if(p.get('view')==='episodes')rows=episodes.filter(e=>!p.get('season')||e.season===p.get('season'));
      else {
        rows=p.get('kind')==='movie'?films:p.get('kind')==='series'?series:p.get('kind')==='all'?all:tv;
        if(p.get('favorites')==='1')rows=rows.filter(i=>favorites.has(i.id));
        const norm=s=>s.normalize('NFD').replace(/\p{M}/gu,'').toUpperCase();
        if(p.get('q'))rows=rows.filter(i=>norm(i.name+' '+i.group).includes(norm(p.get('q'))));
      }
      rows=rows.map(i=>({...i,favorite:favorites.has((i.kind==='episode'||i.kind==='season')?'s20':i.id)}));
      const limit=Number(p.get('limit')||10),offset=Math.min(Number(p.get('offset')||0),Math.max(0,Math.floor((rows.length-1)/limit)*limit));
      return {items:rows.slice(offset,offset+limit),total:rows.length,offset};
    }
    throw Error('Unexpected fake request '+url);
  }
  const window={innerHeight:576,setTimeout(fn,ms){timers.set(++timer,{fn,ms});return timer;},clearTimeout(id){timers.delete(id);},localStorage:{getItem:k=>storage[k]||null,setItem:(k,v)=>{storage[k]=v;}}};
  if(native)window.gSTB={InitPlayer(){calls.push(['Init']);},Stop(){calls.push(['Stop']);if(opts.stopFails)throw Error('stop');},Play(url){calls.push(['Play',url]);},GetPosTime(){return position;},GetMediaLen(){return 3600;},SetPosTime(pos){calls.push(['Seek',pos]);position=pos;},Pause(){calls.push(['Pause']);},Continue(){calls.push(['Continue']);},SetTopWin(){},EnableSpatialNavigation(){},EnableVKButton(){}};
  if(native){
    window.gSTB.GetAudioPIDsEx=()=>opts.audioTracks===undefined?"[{pid:101,lang:[\"por\",\"pt\"],type:4,title:'Principal'}, {pid:102,lang:[\"eng\",\"en\"],type:3}]":opts.audioTracks;
    window.gSTB.GetAudioPIDs=()=>opts.fallbackAudio||'[]';
    window.gSTB.GetSubtitlePIDs=()=>opts.subtitleTracks===undefined?'[{pid:201,lang:["por", "pt"]},{pid:202,lang:["eng", "en"]}]':opts.subtitleTracks;
    window.gSTB.GetAudioPID=()=>101;window.gSTB.GetSubtitlePID=()=>201;
    window.gSTB.SetAudioPID=pid=>{calls.push(['Audio',pid]);};
    window.gSTB.SetSubtitlePID=pid=>{calls.push(['Subtitle',pid]);};
    window.gSTB.SetSubtitles=value=>{calls.push(['Subtitles',value]);};
    window.gSTB.GetVolume=()=>50;window.gSTB.SetVolume=value=>{calls.push(['Volume',value]);};
    window.gSTB.GetMute=()=>false;window.gSTB.SetMute=value=>{calls.push(['Mute',value]);};
    if(opts.player)Object.assign(window.gSTB,opts.player);
  }
  function XHR(){
    this.open=(method,url)=>{this.method=method;this.url=url;};this.setRequestHeader=(k,v)=>{this.headers[k]=v;};this.headers={};
    this.abort=()=>{this.aborted=true;};
    this.complete=()=>{const result=respond(this.url,this.body);this.status=result?200:403;this.readyState=4;this.responseText=JSON.stringify(result);this.onreadystatechange();};
    this.send=body=>{if(opts.sendThrows)throw Error('transport unavailable');this.body=body?JSON.parse(body):null;requests.push({url:this.url,method:this.method,body:this.body,headers:this.headers});if(opts.defer&&opts.defer(this.url)){pending.push(this);}else this.complete();};
  }
  const ctx={window,document:{body:{style:{}},documentElement:{clientHeight:576},getElementById:id=>{assert(nodes[id],'Missing actual HTML id '+id);return nodes[id];},createElement:tag=>new Element(tag),createTextNode:value=>({value})},XMLHttpRequest:XHR};
  ctx.Date=class extends Date{constructor(...args){super(...(args.length?args:[clock]));}};
  vm.createContext(ctx);vm.runInContext(fs.readFileSync('public/tv/browse-prefs.js','utf8'),ctx);vm.runInContext(mediaTracks,ctx);if(!opts.missingScript)vm.runInContext(source,ctx);vm.runInContext(boot,ctx);
  return {nodes,calls,requests,pending,favorites,storage,ctx,
    key(code,extra={}){ctx.MagPortal.keydown({keyCode:code,preventDefault(){},...extra});},
    release(code){ctx.document.onkeyup({keyCode:code,preventDefault(){}});},
    advance(ms){clock+=ms;},
    setPosition(pos){position=pos;},
    type(s){for(const c of s)ctx.MagPortal.keypress({charCode:c.charCodeAt(0),preventDefault(){}});},
    click(id){nodes[id].onclick();},
    flush(ms){for(const[id,t]of Array.from(timers))if(t.ms===ms){timers.delete(id);t.fn();}},
    enterTV(){this.key(13);}
  };
}
// Startup must not wait for onload, aggregate metadata or native InitPlayer.
let h=harness(true,{defer:u=>u==='/api/library'});
assert.match(h.nodes['selected-name'].value,/Todos/);
assert.match(h.nodes.group.value,/Portugal/);
assert.equal(h.ctx.window.onload,undefined);
assert(!h.calls.some(c=>c[0]==='Init'));
assert.equal(h.requests.filter(r=>r.url.startsWith('/api/catalog')).length,1);
assert(h.requests[0].url.includes('view=groups'));assert(h.requests[0].url.includes('country=PT'));
h.ctx.MagPortal.init();assert.equal(h.requests.length,3);
h.flush(15000);assert.match(h.nodes['library-counts'].value,/indisponível/);
h=harness(false,{defer:u=>u.startsWith('/api/catalog')});h.flush(15000);assert.match(h.nodes.group.value,/MENU para repetir/);
h=harness(false,{sendThrows:true});assert.match(h.nodes.group.value,/MENU para repetir/);
h=harness(false,{missingScript:true});assert.match(h.nodes.group.value,/Interface não carregada/);
h=harness(false);assert.match(h.nodes['selected-name'].value,/Todos/);h.enterTV();assert.match(h.nodes['selected-name'].value,/Canal 1/);h.key(13);assert(!h.requests.some(r=>r.url==='/api/media/mag'));assert.match(h.nodes.status.value,/computador/);
h.key(34);assert.match(h.nodes['selected-name'].value,/Canal 11/);h.key(8);assert.match(h.nodes['selected-name'].value,/Todos/);h.key(8);assert.equal(h.nodes['selected-name'].value,'Portugal');

h=harness(false);h.click('tab-movie');h.key(13);h.key(114);h.type('camara');h.key(13);assert.match(h.nodes['selected-name'].value,/Câmara/);assert(h.requests.at(-1).url.includes('q=camara'));assert(!h.requests.some(r=>r.url==='/api/media/mag'));
h.key(8);h.key(114);h.key(13);assert.equal(h.nodes['search-query'].value,'A');h.key(115);assert(h.requests.at(-1).url.includes('q=A'));

// Live search: debounce letters, keep keyboard open, backspace/clear and cancel.
h=harness(false);h.click('tab-movie');h.key(114);
let countBefore=h.requests.length;h.type('camara');assert.equal(h.requests.length,countBefore);
h.flush(250);assert.equal(h.nodes['search-panel'].style.display,'block');assert.match(h.nodes['selected-name'].value,/Câmara/);
assert(h.requests.at(-1).url.includes('q=camara'));h.type('zz');h.flush(250);assert.equal(h.nodes['selected-name'].value,'Sem resultados');
h.key(8);h.key(8);h.flush(250);assert.match(h.nodes['selected-name'].value,/Câmara/);
h.key(27);h.flush(250);assert.equal(h.nodes['search-panel'].style.display,'none');assert.match(h.nodes['selected-name'].value,/Todos/);
assert(!h.requests.some(r=>r.url==='/api/media/mag'));
h=harness();h.enterTV();h.key(114);h.key(13);h.flush(250);assert(h.requests.at(-1).url.includes('q=A'));
h.flush(650);assert(!h.requests.some(r=>r.url.startsWith('/api/epg/')));
// Action keys are three columns; DOWN reaches Clear, then the last action row.
for(let i=0;i<6;i++)h.key(40);h.key(39);h.key(39);h.key(13);h.flush(250);
assert.equal(h.nodes['selected-name'].value,'Canal 1 FHD');assert(!h.requests.at(-1).url.includes('q='));
h.key(40);h.key(13);assert.equal(h.nodes['search-panel'].style.display,'none');
h=harness();h.enterTV();h.key(114);h.type('Canal 1');h.flush(250);h.flush(650);
assert(!h.requests.some(r=>r.url.startsWith('/api/epg/')));
h.key(115);h.flush(650);assert.match(h.nodes.epg.value,/Programa real/);
h.key(89);assert.equal(h.nodes['info-panel'].style.display,'block');assert.match(h.nodes['info-text'].value,/Programa real/);
// A superseded search cannot overwrite newer results or a different section.
let searchDelay=false;h=harness(false,{defer:u=>searchDelay&&u.startsWith('/api/catalog')});
h.click('tab-movie');h.key(114);searchDelay=true;h.type('cam');h.flush(250);h.type('zz');h.flush(250);
h.pending[1].complete();h.pending[0].complete();assert.equal(h.nodes['selected-name'].value,'Sem resultados');
h.type('next');h.click('tab-series');h.flush(250);h.pending[2].complete();assert.match(h.nodes.group.value,/Séries/);

h=harness();h.enterTV();h.key(113);assert(h.favorites.has('1'));const mutation=h.requests.find(r=>r.url==='/api/favorite');assert.equal(mutation.headers['X-MAG-Action'],'fixture-action');h.key(115);assert.match(h.nodes['selected-name'].value,/Canal 1/);assert.match(h.nodes['counter'].value,/1 de 1/);h.advance(800);h.key(113);assert.match(h.nodes['selected-name'].value,/Sem resultados/);
h=harness(true,{failFavorite:true});h.enterTV();h.key(113);assert.match(h.nodes.status.value,/Não foi possível guardar/);assert.equal(h.favorites.size,0);

h=harness();h.enterTV();h.click('quality-button');h.key(40);h.key(40);h.key(40);h.key(13);assert.equal(h.storage['mag-quality-v2'],'FHD');assert(h.requests.at(-1).url.includes('quality=FHD'));
h.click('quality-button');assert.match(h.nodes['picker-list'].children[3].className,/selected/);assert.match(h.nodes['picker-list'].children[3].value,/Em uso/);assert.match(h.nodes['picker-description'].value,/Full HD/);h.key(8);
h=harness();h.enterTV();h.key(13);h.key(9);h.key(9);h.flush(1000);assert.equal(h.calls.filter(c=>c[0]==='Play').length,1);assert.equal(h.requests.filter(r=>r.url==='/api/media/mag').length,1);assert(h.requests.some(r=>r.url==='/api/media/mag'&&r.body.id==='3'));h.key(8);assert.equal(h.calls.at(-1)[0],'Stop');
h=harness();h.enterTV();h.key(13);h.key(8);h.flush(1000);assert.equal(h.calls.filter(c=>c[0]==='Play').length,0);
h=harness(true,{stopFails:true});h.enterTV();h.key(13);h.flush(1000);assert.equal(h.calls.filter(c=>c[0]==='Play').length,0);

h=harness();h.click('tab-series');h.key(13);assert.equal(h.nodes['selected-name'].value,'Uma série');h.key(13);assert.match(h.nodes['selected-name'].value,/Temporada 1/);h.key(13);assert.match(h.nodes['selected-name'].value,/T1 E1/);assert(!h.requests.some(r=>r.url==='/api/media/mag'));h.key(13);h.flush(1000);assert(h.requests.some(r=>r.url==='/api/media/mag'&&r.body.id==='e201'));h.key(32);assert.equal(h.calls.at(-1)[0],'Pause');h.key(32);assert.equal(h.calls.at(-1)[0],'Continue');h.ctx.stbEvent.onEvent(1);h.flush(300);assert.equal(h.nodes.menu.style.display,'block');

h=harness();h.enterTV();h.flush(650);assert.match(h.nodes.epg.value,/Programa real/);assert(!h.requests.some(r=>r.url==='/api/media/mag'));
h.key(89);assert.equal(h.nodes['info-panel'].style.display,'block');assert.match(h.nodes['info-text'].value,/Programa real/);h.key(8);
h.key(13);h.flush(1000);h.ctx.stbEvent.onEvent(2);assert.equal(h.nodes.menu.style.display,'none');h.ctx.stbEvent.onEvent(5);h.flush(0);assert.equal(h.nodes.menu.style.display,'block');
h=harness();h.key(122);for(let i=0;i<7;i++)h.key(40);h.key(13);assert.equal(h.nodes.help.style.display,'block');h.key(8);assert.equal(h.nodes.help.style.display,'none');

let delay=false;h=harness(false,{defer:u=>delay&&u.startsWith('/api/catalog')});delay=true;h.click('tab-movie');h.click('tab-series');h.pending[1].complete();h.pending[0].complete();assert.match(h.nodes.group.value,/Séries/);assert(!h.requests.some(r=>r.url==='/api/media/mag'));
// Catalog refresh never stops/restarts the player or changes the selected page.
h=harness();h.enterTV();h.key(13);h.flush(1000);
const beforeCalls=h.calls.length,beforePage=h.requests.filter(r=>r.url.startsWith('/api/catalog')).length;
h.click('update-button');assert.match(h.nodes['update-status'].value,/A verificar filmes/);
assert.equal(h.calls.length,beforeCalls);h.flush(3000);
assert.equal(h.calls.length,beforeCalls);assert.equal(h.requests.filter(r=>r.url.startsWith('/api/catalog')).length,beforePage);
assert.match(h.nodes['update-status'].value,/12 canais, 35 filmes e 4 séries/);
assert.equal(h.requests.find(r=>r.url==='/api/refresh'&&r.method==='POST').headers['X-MAG-Action'],'fixture-action');
h=harness(false,{refreshStatus:{running:false,error:'Falha. Catálogo preservado.',last_success:'2026-11-01T20:00:00Z'}});
assert.match(h.nodes['update-status'].value,/preservado/);assert.match(h.nodes['update-status'].value,/2026-11-01/);
h.key(122);for(let i=0;i<10;i++)h.key(40);h.key(13);
assert.equal(h.nodes['source-panel'].style.display,'block');assert.match(html,/id="source-input" type="password"/);
h.nodes['source-input'].value='http://fixture.invalid/get.php?username=fixture&password=secret';h.key(13);
assert.equal(h.nodes['source-input'].value,'');assert.equal(h.nodes['source-panel'].style.display,'none');
// Resume only after native play-start; save without disturbing playback.
h=harness(true,{resume:90});h.click('tab-movie');h.key(13);h.key(13);h.flush(1000);h.ctx.stbEvent.onEvent(4);
assert(!h.calls.some(c=>c[0]==='Seek'));h.flush(200);assert.deepEqual(h.calls.at(-1),['Seek',90]);h.flush(800);h.setPosition(120);h.flush(30000);
assert.equal(h.requests.filter(r=>r.url==='/api/progress').at(-1).body.position,120);
h.setPosition(3600);h.ctx.stbEvent.onEvent(1);h.flush(300);assert.equal(h.requests.filter(r=>r.url==='/api/progress').at(-1).body.completed,true);
function moviePlaying(options={}){const app=harness(true,options);app.click('tab-movie');app.key(13);app.key(13);app.flush(1000);app.ctx.stbEvent.onEvent(2);app.ctx.stbEvent.onEvent(4);return app;}
function playbackOption(app,index){app.key(122);for(let i=0;i<index;i++)app.key(40);app.key(13);}
// Progressive seeking previews a target; release commits exactly once without a new stream.
h=moviePlaying();h.key(39);assert.match(h.nodes['osd-title'].value,/2:05.*Solte/);
assert(!h.calls.some(c=>c[0]==='Seek'));h.release(39);h.flush(200);assert.deepEqual(h.calls.at(-1),['Seek',125]);
const playCalls=h.calls.filter(c=>c[0]==='Play'||c[0]==='Stop').length;
h.flush(800);h.key(37);h.release(37);h.flush(200);assert.deepEqual(h.calls.at(-1),['Seek',120]);
h.flush(800);h.key(39);h.release(39);h.flush(200);assert.deepEqual(h.calls.at(-1),['Seek',125]);
h=moviePlaying();h.key(39);h.key(39);assert.match(h.nodes['osd-title'].value,/2:05/); // throttle duplicate event
h.advance(500);h.key(39);assert.match(h.nodes['osd-title'].value,/2:10/);
h.advance(1100);h.key(39);assert.match(h.nodes['osd-title'].value,/2:20/);
h.advance(2000);h.key(39);assert.match(h.nodes['osd-title'].value,/2:50/);
assert(!h.calls.some(c=>c[0]==='Seek'));h.release(37);h.flush(200);assert(!h.calls.some(c=>c[0]==='Seek'));
h.release(39);h.flush(200);assert.deepEqual(h.calls.at(-1),['Seek',170]);assert.equal(h.calls.filter(c=>c[0]==='Seek').length,1);
assert.equal(h.calls.filter(c=>c[0]==='Play'||c[0]==='Stop').length,playCalls);
assert.equal(h.requests.filter(r=>r.url==='/api/media/mag').length,1);
// Reversing resets acceleration but preserves preview position; no keyup has a bounded fallback.
h=moviePlaying();h.key(39);h.advance(3600);h.key(39);h.key(37);h.release(37);h.flush(200);assert.deepEqual(h.calls.at(-1),['Seek',150]);
h=moviePlaying();h.key(39);h.flush(900);h.flush(200);assert.deepEqual(h.calls.at(-1),['Seek',125]);h.release(39);h.flush(200);assert.equal(h.calls.filter(c=>c[0]==='Seek').length,1);
h.key(39);h.key(8);h.release(39);h.flush(200);h.flush(900);h.flush(200);assert.equal(h.calls.filter(c=>c[0]==='Seek').length,1);
h=moviePlaying();h.key(39);h.key(122);h.flush(200);assert.deepEqual(h.calls.at(-1),['Seek',125]);h.release(39);h.flush(200);assert.equal(h.calls.filter(c=>c[0]==='Seek').length,1);
h=moviePlaying({player:{GetMediaLen:()=>123}});h.key(39);h.release(39);h.flush(200);assert.deepEqual(h.calls.at(-1),['Seek',122]);
h=moviePlaying({player:{GetPosTime:()=>2}});h.key(37);h.release(37);h.flush(200);assert.deepEqual(h.calls.at(-1),['Seek',0]);
h=moviePlaying({player:{GetMediaLen:()=>0}});h.key(39);h.release(39);h.flush(200);h.flush(900);h.flush(200);assert(!h.calls.some(c=>c[0]==='Seek'));assert.match(h.nodes['osd-title'].value,/indisponível/);
h=moviePlaying({player:{SetPosTime:()=>false}});h.key(39);h.release(39);h.flush(200);assert.match(h.nodes['osd-title'].value,/não permite/);
h=harness();h.enterTV();h.key(13);h.flush(1000);h.ctx.stbEvent.onEvent(4);h.key(39);h.release(39);h.flush(200);h.flush(900);h.flush(200);assert(!h.calls.some(c=>c[0]==='Seek'));
// Native callbacks can be synchronous: reproduce the physical failure paths without streams.
h=moviePlaying();let inNative=false,nativeStops=0,nativeSeeks=0;
h.ctx.window.gSTB.Stop=function(){assert(!inNative,'Stop re-entered a native callback');nativeStops++;h.ctx.stbEvent.onEvent(1);};
h.ctx.window.gSTB.SetPosTime=function(target){nativeSeeks++;inNative=true;h.ctx.stbEvent.onEvent(1);h.ctx.stbEvent.onEvent(4);inNative=false;h.setPosition(target);};
h.key(39);h.release(39);h.flush(200);assert.equal(nativeSeeks,1);assert.equal(nativeStops,0);
assert(!h.requests.some(r=>r.url==='/api/progress'&&r.body.completed));
h.key(39);h.release(39);h.flush(200);assert.equal(nativeSeeks,1);assert.match(h.nodes['osd-title'].value,/aguardar/);
h.flush(800);assert.equal(h.nodes.menu.style.display,'none');h.key(8);assert.equal(nativeStops,1);assert.equal(h.nodes.menu.style.display,'block');
// Resume consumes its saved position before calling native seek and outside event dispatch.
h=harness(true,{resume:90});nativeSeeks=0;
h.ctx.window.gSTB.SetPosTime=function(target){assert(!inNative);nativeSeeks++;h.ctx.stbEvent.onEvent(4);h.setPosition(target);};
h.click('tab-movie');h.key(13);h.key(13);h.flush(1000);inNative=true;h.ctx.stbEvent.onEvent(4);inNative=false;
assert.equal(nativeSeeks,0);h.flush(200);h.flush(800);h.flush(200);assert.equal(nativeSeeks,1);
// A silent/stuck seek returns to the list in 12s; BACK also cancels immediately.
h=moviePlaying({player:{SetPosTime:function(){}}});h.key(39);h.release(39);h.flush(200);h.advance(12000);h.flush(800);
assert.equal(h.nodes.menu.style.display,'block');assert.match(h.nodes.status.value,/não retomou/);assert(!h.requests.some(r=>r.url==='/api/progress'&&r.body.completed));
h=moviePlaying({player:{SetPosTime:function(){}}});h.key(39);h.release(39);h.flush(200);h.key(8);h.advance(12000);h.flush(800);assert.equal(h.nodes.menu.style.display,'block');assert.equal(h.calls.filter(c=>c[0]==='Stop').length,2);
// Native errors defer Stop; event1 at a discontinuity does not falsely complete a title.
h=moviePlaying();nativeStops=0;h.ctx.window.gSTB.Stop=function(){assert(!inNative);nativeStops++;h.ctx.stbEvent.onEvent(1);};
inNative=true;h.ctx.stbEvent.onEvent(5);inNative=false;assert.equal(nativeStops,0);h.flush(0);assert.equal(nativeStops,1);
h=moviePlaying();h.ctx.stbEvent.onEvent(1);h.flush(300);assert.equal(h.requests.filter(r=>r.url==='/api/progress').at(-1).body.completed,false);
h=moviePlaying();h.ctx.stbEvent.onEvent(1);h.ctx.stbEvent.onEvent(4);h.flush(300);assert.equal(h.nodes.menu.style.display,'none');
// A seek genuinely reaching the final frame completes after leaving the native callback.
h=moviePlaying({player:{GetMediaLen:()=>123}});h.ctx.window.gSTB.SetPosTime=function(target){h.setPosition(target);h.ctx.stbEvent.onEvent(1);};
h.key(39);h.release(39);h.flush(200);h.flush(800);assert.equal(h.nodes.menu.style.display,'block');assert.equal(h.requests.filter(r=>r.url==='/api/progress').at(-1).body.completed,true);
// Cancelled event handling cannot stop a later playback session.
h=moviePlaying();h.ctx.stbEvent.onEvent(1);h.key(8);h.key(13);h.flush(1000);h.ctx.stbEvent.onEvent(4);h.flush(300);assert.equal(h.nodes.menu.style.display,'none');
// Physical regression: no native seek occurs inside keydown/keyup, even on release.
h=moviePlaying();let insideKey=true,seekOutside=0;
h.ctx.window.gSTB.SetPosTime=function(target){assert(!insideKey);seekOutside++;h.setPosition(target);};
h.key(39);h.release(39);assert.equal(seekOutside,0);insideKey=false;h.flush(200);assert.equal(seekOutside,1);
// Local diagnostics contain only typed checkpoints; loss or delay never traps playback.
let trace=h.requests.filter(r=>r.url==='/api/player-diagnostics');assert(trace.some(r=>r.body.stage==='seek_call'));assert(trace.some(r=>r.body.stage==='seek_return'));assert(!JSON.stringify(trace.map(r=>r.body)).includes('fixture.invalid'));
h=moviePlaying({failDiagnostics:true});h.key(39);h.release(39);h.flush(200);assert.deepEqual(h.calls.at(-1),['Seek',125]);
h=moviePlaying({defer:u=>u==='/api/player-diagnostics'});h.key(39);h.release(39);h.flush(200);assert(!h.calls.some(c=>c[0]==='Seek'));h.flush(700);assert.deepEqual(h.calls.at(-1),['Seek',125]);
h=moviePlaying({defer:u=>u==='/api/player-diagnostics'});h.key(39);h.release(39);h.flush(200);h.key(8);h.pending.forEach(r=>r.complete());h.flush(700);assert(!h.calls.some(c=>c[0]==='Seek'));
// Fast mode is driven by a timer, not remote key repeats; OK sends one deferred seek.
h=moviePlaying();h.key(70,{altKey:true});h.release(70);h.flush(200);assert.match(h.nodes['osd-title'].value,/Nível 1.*2:10/);
h.flush(500);h.flush(500);assert.match(h.nodes['osd-title'].value,/2:30/);
h.advance(400);h.key(70,{altKey:true});h.release(70);h.flush(500);assert.match(h.nodes['osd-title'].value,/Nível 2.*3:30/);
h.advance(400);h.key(102,{altKey:true});h.release(102);h.flush(500);assert.match(h.nodes['osd-title'].value,/Nível 3.*5:30/);
assert(!h.calls.some(c=>c[0]==='Seek'));h.key(13);assert(!h.calls.some(c=>c[0]==='Seek'));h.flush(200);assert.deepEqual(h.calls.at(-1),['Seek',330]);h.flush(500);assert.equal(h.calls.filter(c=>c[0]==='Seek').length,1);h.flush(800);
assert.equal(h.calls.filter(c=>c[0]==='Play').length,1);assert.equal(h.calls.filter(c=>c[0]==='Stop').length,1);
// BACK cancels the preview without stopping the video or moving playback.
h=moviePlaying();h.key(66,{altKey:true});h.release(66);h.flush(500);h.key(8);h.flush(500);h.flush(200);assert.equal(h.nodes.menu.style.display,'none');assert(!h.calls.some(c=>c[0]==='Seek'));assert.equal(h.calls.filter(c=>c[0]==='Stop').length,1);
// Direction reversal and fine adjustment, bounded targets, persistent OSD at the end.
h=moviePlaying();h.key(70,{altKey:true});h.key(98,{altKey:true});assert.match(h.nodes['osd-title'].value,/Recuar.*2:00/);h.key(39);h.release(39);h.flush(200);assert.deepEqual(h.calls.at(-1),['Seek',125]);
h=moviePlaying({player:{GetMediaLen:()=>125}});h.key(70,{altKey:true});h.release(70);h.flush(5000);assert.equal(h.nodes.osd.style.display,'block');h.key(13);h.flush(200);assert.deepEqual(h.calls.at(-1),['Seek',124]);
h=moviePlaying();playbackOption(h,1);h.key(13);h.flush(500);h.key(13);h.flush(200);assert.deepEqual(h.calls.at(-1),['Seek',140]);
// Favorites are discoverable and work for films, series and the series of a playing episode.
h=harness();h.click('tab-movie');h.key(13);assert.equal(h.nodes['favorite-button'].value,'Guardar filme');h.key(113);assert(h.favorites.has('m10'));assert.equal(h.nodes['favorite-button'].value,'Remover filme');
h.click('tab-series');h.key(13);assert.equal(h.nodes['favorite-button'].value,'Guardar série');h.click('favorite-button');assert(h.favorites.has('s20'));
h.key(115);assert.match(h.nodes['selected-name'].value,/Sem resultados/);h.click('favorites-movie');assert.match(h.nodes['list'].value,/Câmara de Cinema/);assert.doesNotMatch(h.nodes['list'].value,/Uma série/);h.click('favorites-series');assert.match(h.nodes['list'].value,/Uma série/);
h.click('tab-series');h.key(13);h.key(13);assert.equal(h.nodes['favorite-button'].value,'Remover série');h.key(13);h.key(13);h.flush(1000);h.ctx.stbEvent.onEvent(4);h.advance(800);h.key(113);assert(!h.favorites.has('s20'));h.key(8);assert.equal(h.nodes['favorite-button'].value,'Guardar série');
h=moviePlaying({failFavorite:true});h.key(113);assert.match(h.nodes['osd-title'].value,/Não foi possível guardar/);
// MENU exposes search and media favorites using only arrows and OK, no colour keys.
h=harness();h.click('tab-movie');h.key(13);h.key(122);assert.match(h.nodes['picker-list'].children[0].value,/Pesquisar/);assert.match(h.nodes['picker-list'].children[1].value,/Guardar filme/);
h.key(13);assert.equal(h.nodes['search-panel'].style.display,'block');h.key(27);
h.key(122);h.key(40);h.key(13);assert(h.favorites.has('m10'));
h.key(122);h.key(40);h.key(40);h.key(13);assert.match(h.nodes['group'].value,/Favoritos \/ Canais/);h.key(38);h.key(39);h.key(40);assert.match(h.nodes['selected-name'].value,/Câmara de Cinema/);
h.advance(800);h.key(122);h.key(40);h.key(13);assert(!h.favorites.has('m10'));
h=harness();h.click('tab-series');h.key(13);h.key(122);assert.match(h.nodes['picker-list'].children[1].value,/Guardar série/);h.key(40);h.key(13);assert(h.favorites.has('s20'));
h=moviePlaying();playbackOption(h,7);assert(h.favorites.has('m10'));assert.equal(h.calls.filter(c=>c[0]==='Stop').length,1);assert.equal(h.nodes.menu.style.display,'none');
// Audio/subtitles use only tracks actually returned by the native player.
h=moviePlaying();playbackOption(h,2);assert.match(h.nodes['picker-list'].children[0].value,/Português.*AAC/);
h.key(40);h.key(13);assert.deepEqual(h.calls.at(-1),['Audio',102]);
playbackOption(h,3);while(!h.nodes['picker-list'].children[0].className.includes('selected'))h.key(38);
h.key(13);assert.deepEqual(h.calls.at(-1),['Subtitles',false]);
playbackOption(h,3);h.key(40);h.key(13);assert.deepEqual(h.calls.slice(-2),[['Subtitle',201],['Subtitles',true]]);
assert.equal(h.calls.filter(c=>c[0]==='Play').length,1);assert.equal(h.calls.filter(c=>c[0]==='Stop').length,1);
playbackOption(h,4);h.key(13);assert.deepEqual(h.calls.at(-1),['Volume',60]);h.key(192);assert.deepEqual(h.calls.at(-1),['Mute',1]);
playbackOption(h,5);assert.match(h.nodes['picker-description'].value,/ficheiro original/);h.key(8);
h.key(114,{altKey:true});assert.equal(h.calls.at(-1)[0],'Pause');assert.equal(h.nodes['search-panel'].style.display,'none');
h.key(114,{altKey:true});assert.equal(h.calls.at(-1)[0],'Continue');
h.key(49);h.flush(1800);assert.equal(h.calls.filter(c=>c[0]==='Play').length,1);
h=moviePlaying({audioTracks:'[]',subtitleTracks:'[]'});playbackOption(h,2);assert.match(h.nodes['picker-list'].value,/Sem faixas/);
h.key(8);playbackOption(h,3);assert.match(h.nodes['picker-list'].value,/Desligar legendas.*Sem faixas/);
h=moviePlaying({audioTracks:'invalid',fallbackAudio:'[{pid:3,lang:["eng",""]}]'});playbackOption(h,2);h.key(13);assert.deepEqual(h.calls.at(-1),['Audio',3]);
h=moviePlaying({audioTracks:JSON.stringify(Array.from({length:12},(_,i)=>({pid:i+1,lang:['eng']})))});playbackOption(h,2);
assert.equal(h.nodes['picker-list'].children.length,8);h.key(38);assert.equal(h.nodes['picker-list'].children.length,4);h.key(13);assert.deepEqual(h.calls.at(-1),['Audio',12]);
// Legacy descriptor parser handles quoted strings but never executes payloads.
let parsed=h.ctx.MagTracks.read("[{pid:7,lang:['por','pt'],title:'D\\'origem',type:4}]");assert.equal(parsed[0].title,"D'origem");
assert.equal(h.ctx.MagTracks.read('[{pid:1,lang:[],title:(window.injected=1)}]').length,0);assert.equal(h.ctx.window.injected,undefined);
assert.equal(h.ctx.MagTracks.read('[{"pid":1,"lang":[]},{"pid":1},{"pid":99999}]').length,1);
h=moviePlaying({player:{SetAudioPID:()=>{throw Error('unsupported');}}});playbackOption(h,2);h.key(13);assert.match(h.nodes['osd-title'].value,/não conseguiu/);
console.log('PASS: UI/navigation, compact live search, favorites, quality, EPG, refresh/progress; native callback reentrancy/discontinuity, single seek in flight, timeout/recovery, seek bounds/cancellation, media key aliases, audio/subtitle parsing and switching, pagination, volume/mute, unsupported methods. No IPTV connections.');

// Holding the remote favorite key must cause one change, not alternating toggles.
h=harness();h.enterTV();h.key(113);
for(let i=0;i<15;i++){h.advance(100);h.key(113);}
assert(h.favorites.has('1'));assert.equal(h.requests.filter(r=>r.url==='/api/favorite').length,1);
h.advance(800);h.key(113);assert(!h.favorites.has('1'));
// A slow response cannot queue more mutations, even after the debounce interval.
h=harness(true,{defer:u=>u==='/api/favorite'});h.enterTV();h.key(113);h.advance(1000);h.key(113);
assert.equal(h.pending.length,1);h.pending[0].complete();assert(h.favorites.has('1'));
h.advance(800);h.key(113);h.pending[1].complete();assert(!h.favorites.has('1'));
console.log('PASS: favorite key repeats and overlapping requests are ignored; deliberate removal remains available.');

// Favorite groups filter independently and always reopen on channels, including empty groups.
h=harness(true,{favorites:new Set(['1','m10','s20'])});h.key(115);
assert.match(h.nodes.group.value,/Favoritos \/ Canais/);assert.match(h.nodes.list.value,/Canal 1/);
assert.doesNotMatch(h.nodes.list.value,/Cinema|Uma série/);assert.match(h.nodes['tab-all'].className,/active/);
h.key(38);assert.match(h.nodes['favorites-tv'].className,/focused/);h.key(39);
assert.match(h.nodes.group.value,/Favoritos \/ Filmes/);assert.match(h.nodes.list.value,/Câmara de Cinema/);assert.doesNotMatch(h.nodes.list.value,/Canal|Uma série/);
h.key(39);assert.match(h.nodes.group.value,/Favoritos \/ Séries/);h.key(13);h.key(13);
assert.match(h.nodes.list.value,/Temporada 1/);h.key(13);assert.match(h.nodes.list.value,/T1 E1/);assert.equal(h.nodes['favorite-tabs'].style.display,'none');
h.key(8);assert.match(h.nodes.list.value,/Temporada 1/);h.key(8);assert.match(h.nodes.list.value,/Uma série/);assert.equal(h.nodes['favorite-tabs'].style.display,'block');
h.key(115);assert.match(h.nodes.group.value,/Favoritos \/ Canais/);
// MENU route also works with arrows/OK only; search stays within the chosen favorite type.
h.key(122);for(let i=0;i<4;i++)h.key(40);h.key(13);assert.equal(h.nodes['picker-title'].value,'Favoritos');
h.key(40);h.key(13);assert.match(h.nodes.group.value,/Favoritos \/ Filmes/);
h.key(114);h.type('Cinema');h.flush(250);h.key(13);assert.match(h.nodes.list.value,/Câmara de Cinema/);
h.key(8);h.advance(800);h.key(113);assert.match(h.nodes['selected-name'].value,/Sem resultados/);
h.key(38);h.key(37);h.key(40);assert.match(h.nodes.list.value,/Canal 1/);
h.key(112);assert.equal(h.nodes.group.value,'TV / Portugal');assert.equal(h.nodes['favorite-tabs'].style.display,'none');
assert(h.requests.filter(r=>r.url.startsWith('/api/catalog?')&&r.url.includes('favorites=1')).every(r=>!r.url.includes('kind=all')));
console.log('PASS: grouped favorites, default channels, remote/MENU navigation, series return, scoped search and empty groups.');

// Seasons are directories, never streams; pagination and playback remain inside the chosen season.
const seasonEpisodes=Array.from({length:12},(_,i)=>({id:'e'+(300+i),kind:'episode',season:'1',name:'T1 E'+(i+1),group:'Uma série'})).concat([{id:'e400',kind:'episode',season:'2',name:'T2 E1',group:'Uma série'}]);
h=harness(true,{episodes:seasonEpisodes});h.click('tab-series');h.key(13);h.key(13);
assert.match(h.nodes.list.value,/Temporada 1.*12 ep/);assert.match(h.nodes.list.value,/Temporada 2.*1 ep/);
h.key(113);assert(h.favorites.has('s20'));assert.equal(h.nodes['favorite-button'].value,'Remover série');
h.advance(800);h.key(113);assert(!h.favorites.has('s20'));assert.equal(h.nodes['favorite-button'].value,'Guardar série');
assert(!h.requests.some(r=>r.url==='/api/media/mag'));
h.key(13);assert.match(h.nodes.group.value,/Temporada 1/);h.key(34);assert.match(h.nodes.list.value,/T1 E11/);assert.doesNotMatch(h.nodes.list.value,/T2 E1/);
h.key(8);assert.equal(h.nodes['selected-name'].value,'Temporada 1');h.key(40);h.key(13);assert.match(h.nodes.list.value,/T2 E1/);assert.equal(h.nodes.counter.value,'1 de 1 · Página 1/1');
h.key(13);h.flush(1000);assert(h.requests.some(r=>r.url==='/api/media/mag'&&r.body.id==='e400'));h.key(8);h.key(8);assert.equal(h.nodes['selected-name'].value,'Temporada 2');
h.key(8);assert.equal(h.nodes['selected-name'].value,'Uma série');
console.log('PASS: season directories/counts, parent series favorites, per-season pagination and episode playback, nested BACK selection.');

// All left-side controls are reachable with arrows, without executing them while moving.
const sideIds=['tab-tv','tab-movie','tab-series','tab-all','personal-button','collections-button','search-button','favorite-button','quality-button','options-button'];
h=harness();h.enterTV();h.key(40);const selectedBefore=h.nodes['selected-name'].value;h.key(37);
for(let i=0;i<sideIds.length;i++){
  assert.match(h.nodes[sideIds[i]].className,/remote-focus/);
  assert.equal(sideIds.filter(id=>h.nodes[id].className.includes('remote-focus')).length,1);
  assert(!h.nodes.list.children.some(row=>row.className.includes(' selected')));
  assert.equal(h.nodes['selected-name'].value,selectedBefore);h.key(40);
}
assert(!h.requests.some(r=>r.url==='/api/favorite'||r.url==='/api/media/mag'));
h.key(38);h.key(13);assert.equal(h.nodes.picker.style.display,'block');h.key(8);
assert.match(h.nodes['options-button'].className,/remote-focus/);h.key(39);
assert.equal(h.nodes['selected-name'].value,selectedBefore);assert(h.nodes.list.children.some(row=>row.className.includes(' selected')));
h.key(34);assert.match(h.nodes['selected-name'].value,/Canal 12/);h.key(33);assert.equal(h.nodes['selected-name'].value,selectedBefore);
h.key(37);h.key(8);assert.equal(h.nodes['selected-name'].value,selectedBefore);h.key(9);assert.match(h.nodes['options-button'].className,/remote-focus/);h.key(9);assert(!h.nodes['options-button'].className.includes('remote-focus'));
// Select a section, open its list, then use the original search/favorite buttons on that item.
h=harness();h.key(37);h.key(40);h.key(13);assert.equal(h.nodes['selected-name'].value,'Todos os títulos');
h.key(13);assert.equal(h.nodes['selected-name'].value,'Todos os títulos'); // A held OK does not cascade.
h.release(13);h.key(13);assert.equal(h.nodes['selected-name'].value,'Câmara de Cinema');
h.key(37);for(let i=0;i<5;i++)h.key(40);h.key(13);h.release(13);assert.equal(h.nodes['search-panel'].style.display,'block');
h.type('Cinema');h.flush(250);h.key(13);assert.equal(h.nodes['search-panel'].style.display,'none');assert(h.nodes.list.children[0].className.includes(' selected'));
h.key(37);assert.match(h.nodes['search-button'].className,/remote-focus/);h.key(40);h.key(13);
assert(h.favorites.has('m10'));assert.match(h.nodes['favorite-button'].className,/remote-focus/);assert.equal(h.nodes['favorite-button'].value,'Remover filme');
for(let i=0;i<15;i++){h.advance(100);h.key(13);}assert(h.favorites.has('m10'));assert.equal(h.requests.filter(r=>r.url==='/api/favorite').length,1);
h.release(13);h.key(40);h.key(13);assert.equal(h.nodes['picker-title'].value,'Qualidade da TV');h.key(8);h.key(40);h.key(13);assert.equal(h.nodes['picker-title'].value,'Opções');h.key(8);h.key(39);
assert.equal(h.nodes['selected-name'].value,'Câmara de Cinema');assert(!h.requests.some(r=>r.url==='/api/media/mag'));
// Empty lists and late catalog responses must not trap or steal sidebar focus.
h=harness();h.key(115);assert.equal(h.nodes['selected-name'].value,'Sem resultados');h.key(37);assert.match(h.nodes['tab-all'].className,/remote-focus/);h.key(38);h.key(13);h.release(13);assert.match(h.nodes.group.value,/Séries/);
let late=false;h=harness(true,{defer:u=>late&&u.startsWith('/api/catalog')});late=true;h.click('tab-movie');h.key(37);h.pending[0].complete();assert.match(h.nodes['tab-movie'].className,/remote-focus/);
console.log('PASS: sidebar/list arrows, all section/action buttons, stable selection, held OK protection, search return, empty/slow lists and CH page navigation.');

// Portugal is only the default live-TV country; the world and other sections remain accessible.
h=harness(false);assert(h.requests[0].url.includes("country=PT"));h.key(8);assert(h.requests.at(-1).url.includes("view=countries"));h.click("tab-movie");assert(!h.requests.at(-1).url.includes("country=PT"));h.click("tab-series");assert(!h.requests.at(-1).url.includes("country=PT"));h.click("tab-all");assert(!h.requests.at(-1).url.includes("country=PT"));h.click("tab-tv");assert(h.requests.at(-1).url.includes("view=countries"));assert(!h.requests.at(-1).url.includes("country=PT"));h.click("options-button");for(let i=0;i<4;i++)h.key(40);h.key(13);assert(h.requests.at(-1).url.includes("view=countries"));
console.log("PASS: default Portugal for live TV, BACK/MENU world browsing and unchanged movies/series/favorites.");

h=harness(false);h.click('options-button');for(let i=0;i<5;i++)h.key(40);h.key(13);
assert.equal(h.nodes['picker-title'].value,'Origem dos canais');h.key(40);h.key(13);
assert(h.requests.at(-1).url.includes('origin=MEO'));assert.match(h.nodes.group.value,/Origem: MEO/);
assert.equal(h.nodes['picker-title'].value,'Origem dos canais');h.release(13);h.key(40);h.key(13);
assert.equal(new URL('http://fixture.invalid'+h.requests.at(-1).url).searchParams.get('origin'),'MEO,VO');
h.release(13);h.key(38);h.key(13);assert.equal(new URL('http://fixture.invalid'+h.requests.at(-1).url).searchParams.get('origin'),'VO');
h.release(13);h.key(38);h.key(13);assert(!new URL('http://fixture.invalid'+h.requests.at(-1).url).searchParams.get('origin'));h.key(8);

h.click('tab-movie');assert(!h.requests.at(-1).url.includes('origin='));
h.click('tab-tv');assert(!h.requests.at(-1).url.includes('origin='));
console.log('PASS: MAG origins picker uses remote, sends origin filter and resets outside TV.');

h=harness();h.nodes['tab-movie'].onclick();h.nodes['options-button'].onclick();
// Last two options are the VOD country and genre filters.
h.key(38);h.key(13);assert.match(h.nodes['picker-title'].value,/Género/);
h.key(40);h.key(13);assert.ok(h.requests.some(r=>r.url.includes('genre=Drama')&&r.url.includes('kind=movie')));
h.nodes['options-button'].onclick();h.key(38);h.key(38);h.key(13);
assert.match(h.nodes['picker-title'].value,/País/);h.key(40);h.key(13);
assert.ok(h.requests.some(r=>r.url.includes('country=PT')&&r.url.includes('kind=movie')&&!r.url.includes('genre=Drama')));
h.nodes['tab-series'].onclick();assert.ok(h.requests[h.requests.length-1]);
console.log('PASS: MAG VOD genre/country pickers via remote, combined query and country reset.');

h=harness();h.nodes['tab-series'].onclick();h.key(13);h.key(13);
h.nodes['options-button'].onclick();h.key(38);h.key(13);h.key(40);h.key(13);
const filteredSeries=h.requests.filter(r=>r.url.includes('/api/catalog?')).at(-1).url;
assert.ok(filteredSeries.includes('kind=series')&&filteredSeries.includes('genre=Drama')&&filteredSeries.includes('view=items'));
assert.equal(new URL('http://fixture.invalid'+filteredSeries).searchParams.get('group')||'','');
console.log('PASS: MAG genre filter from seasons returns to series without treating series title as category.');

// Switching source preserves the selected semantic category, even with no matches.
h=harness(false,{groups:[{id:'group:Desporto',name:'Desporto',kind:'group',group:'Desporto',count:12}]});
h.key(13);assert.equal(new URL('http://fixture.invalid'+h.requests.at(-1).url).searchParams.get('group'),'Desporto');
h.click('options-button');for(let i=0;i<5;i++)h.key(40);h.key(13);h.key(40);h.key(13);
assert.equal(new URL('http://fixture.invalid'+h.requests.at(-1).url).searchParams.get('group'),'Desporto');
assert.equal(new URL('http://fixture.invalid'+h.requests.at(-1).url).searchParams.get('origin'),'MEO');
console.log('PASS: MAG source switch preserves selected category.');

// Same language fixtures as the shared backend, plus native lifecycle protection.
for(const [rows,expected] of JSON.parse(fs.readFileSync(path.join(__dirname,'audio-preference-cases.json'),'utf8'))){
 const tracks=rows.map((t,i)=>({pid:100+i,lang:[t.language],title:t.title||''}));
 const selected=h.ctx.MagTracks.preferred(tracks);assert.equal(selected?selected.pid-100:null,expected);
}
h=moviePlaying();assert.equal(h.calls.filter(c=>c[0]==='Audio').length,0,'Never switch from inside native callback');
h.flush(250);assert.deepEqual(h.calls.at(-1),['Audio',102]);
h.ctx.stbEvent.onEvent(4);h.flush(250);assert.equal(h.calls.filter(c=>c[0]==='Audio').length,1,'Seek does not override selected audio');
h=moviePlaying();playbackOption(h,2);h.key(13);h.flush(250);assert.deepEqual(h.calls.filter(c=>c[0]==='Audio'),[['Audio',101]],'Manual choice cancels pending auto');
h=moviePlaying({audioTracks:'[{pid:101,lang:["eng"]},{pid:103,lang:["por"],title:"Português Portugal"}]'});h.flush(250);assert.deepEqual(h.calls.at(-1),['Audio',103]);
h=moviePlaying({audioTracks:'[{pid:101,lang:["spa"]},{pid:103,lang:["por"]}]'});h.flush(250);assert.equal(h.calls.filter(c=>c[0]==='Audio').length,0,'Unmatched languages preserve native original');
h=moviePlaying();h.key(8);h.flush(250);assert.equal(h.calls.filter(c=>c[0]==='Audio').length,0,'Closing cancels preference');
h=harness();h.enterTV();h.key(13);h.flush(1000);h.ctx.stbEvent.onEvent(4);h.flush(250);assert.equal(h.calls.filter(c=>c[0]==='Audio').length,0,'Live TV unchanged');
let reads=0;h=moviePlaying({player:{GetAudioPIDsEx:()=>{reads++;return reads>1?'[{pid:103,lang:["eng"]}]':'[]';}}});h.flush(250);h.flush(250);assert.deepEqual(h.calls.at(-1),['Audio',103]);
console.log('PASS automatic PT-PT / English preference, original fallback, deferred native selection, manual override, delayed descriptors, stop and live TV protection.');

// Filters survive a fresh portal instance and section switches, without autoplay.
h=harness(false);h.click('options-button');for(let i=0;i<5;i++)h.key(40);h.key(13);h.key(40);h.key(13);h.release(13);h.key(40);h.key(13);h.key(8);
const savedPreferences=h.storage;h=harness(false,{storage:savedPreferences});assert.equal(new URL('http://fixture.invalid'+h.requests.find(r=>r.url.startsWith('/api/catalog?')).url).searchParams.get('origin'),'MEO,VO');
h.click('tab-movie');h.click('tab-tv');assert.equal(new URL('http://fixture.invalid'+h.requests.at(-1).url).searchParams.get('origin'),'MEO,VO');assert.equal(h.calls.filter(c=>c[0]==='Play').length,0);
console.log('PASS: MAG multiple origins restored across portal instances and section switches; no autoplay.');
