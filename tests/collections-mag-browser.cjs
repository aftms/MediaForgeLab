/* Legacy capability simulation only; never claims physical MAG playback. */
const fs=require('fs'),assert=require('assert/strict'),sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 const fixture=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
 const port=fs.readFileSync(process.argv[3]+'/DevToolsActivePort','utf8').split('\n')[0];
 const tabs=await(await fetch('http://127.0.0.1:'+port+'/json')).json();const socket=new WebSocket(tabs.find(t=>t.type==='page').webSocketDebuggerUrl);
 await new Promise(r=>socket.onopen=r);let sequence=0;const pending=new Map(),errors=[];
 socket.onmessage=e=>{const d=JSON.parse(e.data);if(d.method==='Fetch.requestPaused'){const css=fs.readFileSync(require('path').join(__dirname,'../public/tv/collections.css'),'utf8').replace(/\binset:[^;}]+;?/g,'');call('Fetch.fulfillRequest',{requestId:d.params.requestId,responseCode:200,responseHeaders:[{name:'Content-Type',value:'text/css'}],body:Buffer.from(css).toString('base64')}).catch(()=>{});}if(d.method==='Runtime.exceptionThrown')errors.push(d.params.exceptionDetails.text);if(d.id&&pending.has(d.id)){const p=pending.get(d.id);pending.delete(d.id);clearTimeout(p.timer);d.error?p.reject(Error(d.error.message)):p.resolve(d.result)}};
 const call=(method,params={})=>new Promise((resolve,reject)=>{const id=++sequence;pending.set(id,{resolve,reject,timer:setTimeout(()=>reject(Error('CDP timeout '+method)),12000)});socket.send(JSON.stringify({id,method,params}))});
 async function run(expression){const r=await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw Error(r.exceptionDetails.exception.description);return r.result.value;}
 async function until(expression){for(let i=0;i<100;i++){if(await run(expression))return;await sleep(80)}throw Error('Timeout: '+expression+' / '+await run(`({status:document.getElementById('status')&&document.getElementById('status').textContent,client:document.body.className,count:document.querySelectorAll('.tile').length})`).then(JSON.stringify));}
 const key=code=>run(`document.onkeydown({which:${code}})`);
 async function open(extra=''){await call('Page.navigate',{url:fixture.url+'/tv/collections.html?client=mag'+extra});await until(`!!window.MFLCollectionShell`);}
 async function listed(){await until(`document.querySelectorAll('.tile').length===3`);}
 async function home(){await until(`location.pathname==='/'`);}
 try{
  await call('Page.enable');await call('Runtime.enable');await call('Network.enable');
  await call('Fetch.enable',{patterns:[{urlPattern:'*collections.css*',requestStage:'Request'}]});
  await call('Network.setBlockedURLs',{urls:['https://*','*/collections/player*']});
  await call('Page.addScriptToEvaluateOnNewDocument',{source:`if(/client=mag/.test(location.search)){
   window.localStorage.removeItem('mfl-browse-v1:collections-mag');Object.defineProperty(XMLHttpRequest.prototype,'onload',{get:function(){return null;},set:function(){}});
   HTMLButtonElement.prototype.click=undefined;Element.prototype.getClientRects=undefined;
   window.nativeCalls=[];window.gSTB={EnableSpatialNavigation:function(v){nativeCalls.push(['spatial',v]);},Stop:function(){nativeCalls.push(['stop']);},InitPlayer:function(){nativeCalls.push(['init']);},SetTopWin:function(v){nativeCalls.push(['top',v]);},Play:function(){nativeCalls.push(['play']);},GetPosTime:function(){return 0;},GetMediaLen:function(){return 60;}};
   if(location.search.indexOf('missing-helper')!==-1)Object.defineProperty(window,'BrowsePrefs',{get:function(){return undefined;},set:function(){}});
   if(location.search.indexOf('failed-api')!==-1){var original=XMLHttpRequest.prototype.open;XMLHttpRequest.prototype.open=function(method,url,async){return original.call(this,method,'/missing-test-endpoint',async);};}
  }`});
  await open();await listed();assert.ok(await run(`nativeCalls.some(function(c){return c[0]==='spatial'&&c[1]===false;})`));
  // Remove unsupported inset, as an old CSS engine would; overlays must still cover the screen.
  await run(`document.getElementById('categories').focus()`);
  await key(13);assert.equal(await run(`document.getElementById('dialog').style.display`),'');
  assert.deepEqual(await run(`(function(){var r=document.getElementById('dialog').getBoundingClientRect();return [r.top,r.left,Math.round(r.right),Math.round(r.bottom)];})()`),await run(`[0,0,document.documentElement.clientWidth,document.documentElement.clientHeight]`));
  await key(40);assert.notEqual(await run('document.activeElement.id'),'dialog-close');await key(8);assert.equal(await run(`document.getElementById('dialog').style.display`),'none');
  await run(`document.getElementById('search').focus()`);await key(13);assert.equal(await run(`document.getElementById('keyboard').style.display`),'');await key(27);assert.equal(await run(`document.getElementById('keyboard').style.display`),'none');
  await run(`document.getElementById('platform').focus()`);await key(13);await key(40);await key(27);assert.equal(await run('location.pathname'),'/tv/collections.html');
  await run(`document.querySelector('.star').focus()`);const before=await run(`document.activeElement.textContent`);await key(13);await until(`document.activeElement.className==='star'&&document.activeElement.textContent!==${JSON.stringify(before)}`);
  await run(`Array.from(document.querySelectorAll('.tile .open')).find(function(n){return n.textContent.indexOf('Vídeo direto')!==-1;}).focus()`);await key(13);
  assert.ok(await run(`nativeCalls.some(function(c){return c[0]==='play';})`));
  assert.equal(await run(`document.getElementById('viewer').getBoundingClientRect().top`),0);
  const stopped=await run(`nativeCalls.filter(function(c){return c[0]==='stop';}).length`);
  await run(`document.getElementById('video').pause=function(){throw Error('Legacy HTML video unavailable');}`);await key(8);
  assert.equal(await run(`document.getElementById('viewer').style.display`),'none');assert.ok(await run(`nativeCalls.filter(function(c){return c[0]==='stop';}).length>${stopped}`));
  await run(`Array.from(document.querySelectorAll('.tile .open')).find(function(n){return n.textContent.indexOf('classificar')!==-1;}).focus()`);await key(13);
  await run(`document.querySelector('#external iframe').focus()`);await until(`document.activeElement.id==='close-viewer'`);await key(8);assert.equal(await run(`document.querySelector('#external iframe')`),null);
  await key(8);await home();
  await open();await listed();await run(`document.getElementById('search').focus()`);await key(8);await home();
  await open();await listed();await run(`document.getElementById('categories').focus()`);await call('Input.dispatchKeyEvent',{type:'keyDown',windowsVirtualKeyCode:13,nativeVirtualKeyCode:13});await call('Input.dispatchKeyEvent',{type:'keyUp',windowsVirtualKeyCode:13,nativeVirtualKeyCode:13});assert.equal(await run(`document.getElementById('dialog').style.display`),'');await key(8);
  await run(`document.getElementById('home').focus()`);await key(13);await home();
  await open();await listed();await run(`document.getElementById('categories').focus()`);await key(13);await key(122);await home();
  await open('&missing-helper');await until(`document.getElementById('status').textContent.indexOf('Voltar')!==-1`);await key(8);await home();
  await call('Network.setBlockedURLs',{urls:['https://*','*/collections/player*','*collections.js*']});await open();await key(8);await home();await call('Network.setBlockedURLs',{urls:['https://*','*/collections/player*']});
  await open('&failed-api');await until(`document.getElementById('status').textContent.length>0`);await key(8);await home();
  await open();await listed();await run(`document.getElementById('categories').onclick=function(){throw Error('Simulated UI failure');};document.getElementById('categories').focus()`);await key(13);assert.ok(await run(`document.getElementById('status').textContent.indexOf('Voltar')!==-1`));await key(8);await home();
  for(const client of ['web','tv']){await call('Page.navigate',{url:fixture.url+'/tv/collections.html?client='+client});await listed();await run(`document.getElementById('categories').click()`);assert.equal(await run(`document.getElementById('dialog').style.display`),'');await run(`document.getElementById('dialog-close').click()`);if(client==='web'){await run(`window.MFLFloating.navigating=function(){return true;};window.MFLFloating.browse=function(){window.browsed=true;};document.getElementById('home').click()`);await sleep(150);assert.equal(await run(`window.browsed&&location.pathname==='/tv/collections.html'`),true);}}
  assert.deepEqual(errors,[]);console.log('PASS: MAG legacy HTTP, OK/arrows/BACK/MENU, favorites, search, select, full overlays, native mock playback/stop after HTML failure, iframe focus, missing helper and API failure exit; web/TV smoke. No external streams played.');
 }finally{socket.close();}
})().catch(e=>{console.error(e.message);process.exit(1)});
