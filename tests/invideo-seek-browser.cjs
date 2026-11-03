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
 await call('Page.enable');await call('Runtime.enable');await call('Emulation.setDeviceMetricsOverride',{width:1280,height:960,deviceScaleFactor:1,mobile:false});
 await call('Page.navigate',{url:fixture.url+'/web/'});await until('document.getElementById("connection") && document.getElementById("connection").textContent!=="A ligar ao computador…"');await sleep(300);
 await run(`document.getElementById('video').muted=true;window.mediaRequests=[];const originalFetch=fetch;window.fetch=function(url,opts){if(typeof url==='string'&&url.endsWith('/api/media/web'))mediaRequests.push(JSON.parse(opts.body));return originalFetch.apply(this,arguments)};document.querySelector('[data-section=movie]').click()`);
 await until('document.querySelector(".card-open")');await run('document.querySelector(".card-open").click()');
 await until('document.getElementById("video").currentTime>0.2 && !document.getElementById("timeline").disabled');
 assert.ok(await run('!document.getElementById("video").controls && document.getElementById("video-stage").contains(document.getElementById("timeline"))'));
 assert.equal(Math.round(await run('Number(document.getElementById("timeline").max)')),120);
 assert.ok(await run('document.getElementById("video").duration < 60'));
 await run('document.getElementById("timeline").scrollIntoView({block:"center"})');
 // Real pointer seek outside the currently prepared HLS window.
 const pos=await run('(()=>{const r=document.getElementById("timeline").getBoundingClientRect();return {x:r.left+r.width*.75,y:r.top+r.height/2}})()');
 await call('Input.dispatchMouseEvent',{type:'mouseMoved',...pos});await call('Input.dispatchMouseEvent',{type:'mousePressed',...pos,button:'left',clickCount:1});await call('Input.dispatchMouseEvent',{type:'mouseReleased',...pos,button:'left',clickCount:1});
 await until('mediaRequests.length===2 && !document.getElementById("timeline").disabled && document.getElementById("video").currentTime>0.2');
 assert.ok(await run('mediaRequests[1].position>85 && mediaRequests[1].position<95'));
 assert.equal(await run('mediaRequests[1].audio'),1,'Auto English preserved across seek');
 await run('var t=document.getElementById("timeline");t.value="8";t.dispatchEvent(new Event("input"));t.dispatchEvent(new Event("change"))');
 await until('mediaRequests.length===3 && !document.getElementById("timeline").disabled && document.getElementById("video").currentTime>0.2');
 assert.equal(await run('mediaRequests[2].position'),8);
 await click('video-toggle');await until('(async()=>!(await(await fetch("/api/media/status")).json()).active)()');
 await run('t.value="60";t.dispatchEvent(new Event("input"));t.dispatchEvent(new Event("change"))');await sleep(200);
 assert.equal(await run('mediaRequests.length'),3,'Paused seek must not open a stream');assert.ok(await run('document.getElementById("play-time").textContent.startsWith("01:00")'));
 await click('video-toggle');await until('mediaRequests.length===4 && !document.getElementById("timeline").disabled && document.getElementById("video").currentTime>0.2');
 assert.equal(await run('mediaRequests[3].position'),60);
 const before=await run('mediaRequests.length');
 await call('Runtime.evaluate',{expression:'document.getElementById("video-screen").click()',userGesture:true});await until('document.fullscreenElement===document.getElementById("video-stage")');
 assert.ok(await run('(()=>{const t=document.getElementById("timeline").getBoundingClientRect();return t.width>innerWidth*.8 && t.bottom<=innerHeight})()'));
 await run('t.value="30";t.dispatchEvent(new Event("input"));t.dispatchEvent(new Event("change"))');
 await until('mediaRequests.length===5 && !document.getElementById("timeline").disabled && document.getElementById("video").currentTime>0.2');
 assert.equal(await run('mediaRequests[4].position'),30);assert.ok(await run('!!document.fullscreenElement'));
 await run('document.exitFullscreen()');await until('!document.fullscreenElement');
 await call('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:false});
 assert.ok(await run('(()=>{const r=document.getElementById("video-stage").getBoundingClientRect(),t=document.getElementById("timeline").getBoundingClientRect();return t.left>=r.left && t.right<=r.right && r.right<=innerWidth})()'));
 const shot=await call('Page.captureScreenshot');fs.writeFileSync(process.argv[3]+'/invideo-seek-mobile.png',Buffer.from(shot.data,'base64'));
 assert.ok(await run('document.getElementById("video").muted'));await click('close-player');await until('(async()=>!(await(await fetch("/api/media/status")).json()).active)()');
 assert.deepEqual(errors,[]);console.log('PASS silent Chrome: full 120s timeline inside video, real pointer seek beyond buffer, backward seek, English preserved, paused seek opens no stream, resume at chosen time, fullscreen seek, mobile fit and lease release.');
 }finally{await run('var b=document.getElementById("close-player");if(b)b.click()');await sleep(300);await call('Browser.close').catch(()=>{});w.close()}
})().catch(e=>{console.error(e.message);process.exit(1)});
