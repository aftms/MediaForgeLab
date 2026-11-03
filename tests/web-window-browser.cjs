const fs=require('fs'),assert=require('assert/strict'),sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 const fixture=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),port=fs.readFileSync(process.argv[3]+'/DevToolsActivePort','utf8').split('\n')[0];
 const tabs=await(await fetch('http://127.0.0.1:'+port+'/json')).json(),w=new WebSocket(tabs.find(t=>t.type==='page').webSocketDebuggerUrl);await new Promise(r=>w.onopen=r);
 let id=0;const pending=new Map(),errors=[];w.onclose=()=>{for(const p of pending.values())p.reject(Error('CDP closed'));pending.clear()};w.onmessage=e=>{const d=JSON.parse(e.data);if(d.method==='Runtime.exceptionThrown')errors.push(d.params.exceptionDetails.text);if(d.id&&pending.has(d.id)){const p=pending.get(d.id);pending.delete(d.id);d.error?p.reject(Error(d.error.message)):p.resolve(d.result)}};
 const call=(method,params={})=>new Promise((resolve,reject)=>{pending.set(++id,{resolve,reject});w.send(JSON.stringify({id,method,params}))});
 async function run(expression){const r=await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;}
 async function until(expr){for(let i=0;i<350;i++){if(await run(expr))return;await sleep(100)}throw Error('Timeout '+expr)}
 const click=id=>run('document.getElementById('+JSON.stringify(id)+').click()');
 async function key(k){await call('Input.dispatchKeyEvent',{type:'keyDown',windowsVirtualKeyCode:k});await call('Input.dispatchKeyEvent',{type:'keyUp',windowsVirtualKeyCode:k});}
 async function browse(client,width,height){await call('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false});await call('Page.navigate',{url:fixture.url+(client==='web'?'/web/personal/':'/tv/personal.html')+'?client='+client});await until('document.querySelectorAll(".tile").length===12');assert.ok(await run('document.documentElement.scrollWidth<=innerWidth'));}
 try{
 await call('Page.enable');await call('Runtime.enable');await call('Emulation.setDeviceMetricsOverride',{width:1500,height:960,deviceScaleFactor:1,mobile:false});
 await call('Page.navigate',{url:fixture.url+'/web/'});await until('document.getElementById("connection").textContent!=="A ligar ao computador…"');await sleep(300);
 await run(`window.mediaRequests=[];var originalFetch=window.fetch;window.fetch=function(url,opts){if(typeof url==='string'&&(url.endsWith('/api/media/web')||url.endsWith('/api/media/stop')))mediaRequests.push(url);return originalFetch.apply(this,arguments)};document.querySelector('[data-section=movie]').click()`);
 await until('document.querySelector(".card-open")');await run('document.querySelector(".card-open").click()');await until('document.getElementById("video").currentTime>1 && !document.getElementById("video").paused');
 const starts=await run('mediaRequests.length'),initial=await run('document.getElementById("player").getBoundingClientRect().width');
 await click('player-smaller');const small=await run('document.getElementById("player").getBoundingClientRect().width');assert.ok(small<initial-100);await click('player-larger');assert.ok(await run('document.getElementById("player").getBoundingClientRect().width')>small+100);
 // Exercise the CSS resize handle with a real pointer drag.
 const rect=await run('(()=>{var r=document.getElementById("player").getBoundingClientRect();return {x:r.right-4,y:r.bottom-4,width:r.width}})()');
 await call('Input.dispatchMouseEvent',{type:'mouseMoved',x:rect.x,y:rect.y});await call('Input.dispatchMouseEvent',{type:'mousePressed',x:rect.x,y:rect.y,button:'left',clickCount:1});await call('Input.dispatchMouseEvent',{type:'mouseMoved',x:rect.x+80,y:rect.y-40,button:'left',buttons:1});await call('Input.dispatchMouseEvent',{type:'mouseReleased',x:rect.x+80,y:rect.y-40,button:'left',clickCount:1});
 assert.ok(await run('document.getElementById("player").getBoundingClientRect().width')>rect.width+30);
 await call('Runtime.evaluate',{expression:'document.getElementById("player-fullscreen").click()',userGesture:true});await until('document.fullscreenElement===document.getElementById("video")');
 assert.ok(await run('document.getElementById("video").getBoundingClientRect().height>=innerHeight-2'));
 await sleep(300);await run('document.exitFullscreen()');await until('!document.fullscreenElement');
 async function doubleClickVideo(){const p=await run('(()=>{var r=document.getElementById("video").getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}})()');for(const n of [1,2]){await call('Input.dispatchMouseEvent',{type:'mousePressed',...p,button:'left',clickCount:n});await call('Input.dispatchMouseEvent',{type:'mouseReleased',...p,button:'left',clickCount:n});await sleep(60)}}
 await doubleClickVideo();await until('document.fullscreenElement===document.getElementById("video")');await doubleClickVideo();await until('!document.fullscreenElement');

 await run('document.getElementById("player").dispatchEvent(new Event("cancel",{cancelable:true}))');assert.ok(await run('document.getElementById("player").open'));
 await call('Emulation.setDeviceMetricsOverride',{width:1100,height:760,deviceScaleFactor:1,mobile:false});await call('Emulation.setDeviceMetricsOverride',{width:1500,height:960,deviceScaleFactor:1,mobile:false});
 await run('document.getElementById("video").pause()');await sleep(150);await run('document.getElementById("video").play();true');await sleep(1100);
 assert.equal(await run('mediaRequests.length'),starts);assert.ok(await run('document.getElementById("video").currentTime>2 && !document.getElementById("video").paused'));
 assert.ok(!(await run('document.getElementById("play-status").textContent')).includes('Use o botão'));const shot=await call('Page.captureScreenshot');fs.writeFileSync(process.argv[3]+'/window-desktop.png',Buffer.from(shot.data,'base64'));
 await run('document.getElementById("video").pause()');await until('document.getElementById("play-status").textContent.includes("ligação libertada")');await until('(async()=>!(await(await fetch("/api/media/status")).json()).active)()');
 const paused=await run('mediaRequests.length');await doubleClickVideo();await until('!!document.fullscreenElement');assert.ok(await run('document.getElementById("video").paused'));await doubleClickVideo();await until('!document.fullscreenElement');await click('player-smaller');await click('player-larger');await sleep(1000);assert.equal(await run('mediaRequests.length'),paused);assert.ok(await run('document.getElementById("video").paused'));
 await call('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:false});assert.ok(await run('document.getElementById("player").getBoundingClientRect().right<=innerWidth && document.getElementById("player").getBoundingClientRect().left>=0'));
 await click('close-player');await sleep(200);assert.deepEqual(errors,[]);console.log('PASS Chrome: button sizes, real corner drag, button and double-click fullscreen enter/exit, paused double-click, viewport resize and transient pause keep one session; sustained pause releases; resizing paused player stays paused; mobile fit.');
 }finally{await run('var b=document.getElementById("close-player");if(b)b.click()');await sleep(300);await call('Browser.close').catch(()=>{});w.close()}
})().catch(e=>{console.error(e.message);process.exit(1)});
