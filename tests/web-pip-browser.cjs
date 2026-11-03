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
 await call('Page.navigate',{url:fixture.url+'/web/'});await until('document.getElementById("connection") && document.getElementById("connection").textContent!=="A ligar ao computador…"');await sleep(300);
 await run(`document.getElementById("video").muted=true;window.mediaRequests=[];var originalFetch=window.fetch;window.fetch=function(url,opts){if(typeof url==='string'&&(url.endsWith('/api/media/web')||url.endsWith('/api/media/stop')))mediaRequests.push(url);return originalFetch.apply(this,arguments)};document.querySelector('[data-section=movie]').click()`);
 await until('document.querySelector(".card-open")');await run('document.querySelector(".card-open").click()');await until('document.getElementById("video").currentTime>1 && !document.getElementById("video").paused');

 const baseline=await run('mediaRequests.length'),position=await run('document.getElementById("video").currentTime');
 assert.ok(await run('!document.getElementById("player-pip").hidden && !document.getElementById("player-pip").disabled'));
 await call('Runtime.evaluate',{expression:'document.getElementById("player-pip").click()',userGesture:true});await until('document.pictureInPictureElement===document.getElementById("video")');
 console.log('PASS entered PiP');assert.equal(await run('document.getElementById("player-pip-label").textContent'),'Repor');await sleep(700);
 assert.ok(await run('document.getElementById("video").currentTime')>position);assert.equal(await run('mediaRequests.length'),baseline);
 await call('Runtime.evaluate',{expression:'document.getElementById("player-pip").click()',userGesture:true});await until('!document.pictureInPictureElement');console.log('PASS returned to page');assert.equal(await run('mediaRequests.length'),baseline);
 await run('document.getElementById("video").pause()');await until('(async()=>!(await(await fetch("/api/media/status")).json()).active)()');
 const paused=await run('mediaRequests.length');await call('Runtime.evaluate',{expression:'document.getElementById("player-pip").click()',userGesture:true});await until('!!document.pictureInPictureElement');assert.ok(await run('document.getElementById("video").paused'));assert.equal(await run('mediaRequests.length'),paused);
 console.log('PASS paused PiP');await click('close-player');await until('!document.pictureInPictureElement');
 assert.deepEqual(errors,[]);console.log('PASS Chrome native PiP: enters/exits, playback progresses, no new stream, paused stays paused, closing player exits PiP. OS stacking/moving requires physical Windows confirmation.');
 }finally{await run('var b=document.getElementById("close-player");if(b)b.click()');await sleep(300);await call('Browser.close').catch(()=>{});w.close()}
})().catch(e=>{console.error(e.message);process.exit(1)});
