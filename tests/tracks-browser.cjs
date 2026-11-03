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
 await call('Page.navigate',{url:fixture.url+'/web/'});await until('document.getElementById("connection").textContent!=="A ligar ao computador…"');await sleep(500);
 await run('document.querySelector("[data-section=movie]").click()');await until('document.querySelector(".card")');
 await run('document.querySelector(".card-open").click()');
 await until('document.querySelector("#media-tracks select").options.length===2 && document.getElementById("video").currentTime>0');
 assert.ok(await run('document.getElementById("media-tracks").textContent.includes("Áudio e legendas")'));
 await run('var subs=document.querySelectorAll("#media-tracks select")[1];subs.value="0";subs.dispatchEvent(new Event("change"))');
 await until('document.getElementById("video").textTracks[0].activeCues && document.getElementById("video").textTracks[0].activeCues.length>0');
 assert.ok(await run('document.getElementById("video").textTracks[0].activeCues[0].text.includes("portuguesa")'));
 console.log('PASS visible Portuguese subtitles');const shot=await call('Page.captureScreenshot');fs.writeFileSync(process.argv[3]+'/tracks-web.png',Buffer.from(shot.data,'base64'));
 await run('document.getElementById("video").pause()');await until('document.getElementById("play-status").textContent.includes("pausa")');
 await run('var a=document.querySelector("#media-tracks select");a.value="1";a.dispatchEvent(new Event("change"));subs.value="1";subs.dispatchEvent(new Event("change"))');
 assert.equal((await(await fetch(fixture.url+'/api/media/status')).json()).active,false);
 console.log('PASS paused selections keep lease free');await run('document.getElementById("video").play();true');await until('document.getElementById("video").textTracks[0].cues && document.getElementById("video").textTracks[0].cues.length>0 && document.getElementById("video").currentTime>0');
 assert.ok(await run('Array.from(document.getElementById("video").textTracks[0].cues).some(c=>c.text.includes("English"))'));
 console.log('PASS English subtitles after resume');await run('subs.value="-1";subs.dispatchEvent(new Event("change"))');await until('document.querySelectorAll("#media-tracks select")[1].value==="-1" && !document.querySelector("#media-tracks select").disabled');
 assert.equal(await run('(document.getElementById("video").textTracks[0].cues||[]).length'),0);
 await click('close-player');await until('(async()=>!(await(await fetch("/api/media/status")).json()).active)()');
 await run(`var testRoot=document.createElement('div');document.body.appendChild(testRoot);var changes=[];var controls=new MediaTrackControls(testRoot,null,()=>2,(a,s)=>changes.push([a,s]),testRoot);controls.update({audio:[{index:0,language:'por'}],subtitles:[{index:0,codec:'hdmv_pgs_subtitle',supported:false}],tracks_known:true,subtitle_index:-1});`);
 assert.ok(await run('Array.from(testRoot.querySelectorAll("select")).every(e=>e.disabled) && testRoot.textContent.includes("ainda não suportado")'));
 await run(`controls.update({audio:[{index:0},{index:1}],subtitles:[{index:0,language:'por',supported:true}],tracks_known:true,subtitle_index:0,cues:[{start:1,end:3,text:'Texto seguro <b>literal</b>'}]});var field=testRoot.querySelector('select');controls.handleKey(13,field);controls.handleKey(39,field);controls.handleKey(13,field);`);
 assert.deepEqual(await run('changes'),[[1,0]]);assert.equal(await run('testRoot.querySelector(".media-captions").querySelector("b")'),null);
 await run('controls.reset();testRoot.remove()');
 await browse('web',390,844);await run('document.querySelector("[data-view=video]").click()');await until('document.querySelectorAll(".tile").length===1');await run('document.querySelector(".tile .open").click()');await until('document.querySelector("#media-tracks select").options.length===2');
 assert.ok(await run('document.querySelector("#media-tracks").getBoundingClientRect().right<=innerWidth'));
 await run('var s=document.querySelectorAll("#media-tracks select")[1];s.value="0";s.dispatchEvent(new Event("change"))');await until('document.getElementById("video").textTracks[0].activeCues && document.getElementById("video").textTracks[0].activeCues.length>0');
 await run('document.querySelector("#media-tracks>button").click()');const mobile=await call('Page.captureScreenshot');fs.writeFileSync(process.argv[3]+'/tracks-personal.png',Buffer.from(mobile.data,'base64'));
 await click('close-viewer');await until('document.getElementById("viewer").style.display==="none"');
 assert.deepEqual(errors,[]);console.log('PASS Chrome: language panel, actual PT/EN timed subtitles, audio change while paused leaves lease free, resume, subtitles off, personal mobile playback and close.');
 }finally{await run('if(window.MagTV)MagTV.suspend();var b=document.getElementById("close-player");if(b)b.click()');await sleep(300);await call('Browser.close').catch(()=>{});w.close()}
})().catch(e=>{console.error(e.message);process.exit(1)});
