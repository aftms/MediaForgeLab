const fs=require('fs'),assert=require('assert/strict'),sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 const fixture=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),port=fs.readFileSync(process.argv[3]+'/DevToolsActivePort','utf8').split('\n')[0];
 const tabs=await(await fetch('http://127.0.0.1:'+port+'/json')).json(),w=new WebSocket(tabs.find(t=>t.type==='page').webSocketDebuggerUrl);await new Promise(r=>w.onopen=r);
 let id=0;const pending=new Map(),errors=[];w.onmessage=e=>{const d=JSON.parse(e.data);if(d.method==='Runtime.exceptionThrown')errors.push(d.params.exceptionDetails.text);if(d.id&&pending.has(d.id)){const p=pending.get(d.id);pending.delete(d.id);d.error?p.reject(Error(d.error.message)):p.resolve(d.result)}};
 const call=(method,params={})=>new Promise((resolve,reject)=>{pending.set(++id,{resolve,reject});w.send(JSON.stringify({id,method,params}))});
 async function run(expression){const r=await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;}
 async function until(expr){for(let i=0;i<350;i++){if(await run(expr))return;await sleep(100)}throw Error('Timeout '+expr)}
 const click=id=>run('document.getElementById('+JSON.stringify(id)+').click()');
 async function key(k){await call('Input.dispatchKeyEvent',{type:'keyDown',windowsVirtualKeyCode:k});await call('Input.dispatchKeyEvent',{type:'keyUp',windowsVirtualKeyCode:k});}
 async function browse(client,width,height){await call('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false});await call('Page.navigate',{url:fixture.url+(client==='web'?'/web/personal/':'/tv/personal.html')+'?client='+client});await until('document.querySelectorAll(".tile").length===12');assert.ok(await run('document.documentElement.scrollWidth<=innerWidth'));}
 try{
  await call('Page.enable');await call('Runtime.enable');await browse('web',1280,720);
  await run('document.querySelector(".tile .actions button").click()');await until('document.querySelector(".tile .actions button").textContent.includes("★")');
  await click('new-album');await run('document.querySelector("#dialog-body input").value="Férias piloto";document.querySelector("#dialog-body > button").click()');await until('document.getElementById("heading").textContent==="Álbuns" && document.querySelector(".tile").textContent.includes("Férias piloto")');
  await run('document.querySelector("[data-view=photo]").click()');await until('document.getElementById("heading").textContent==="Fotografias" && document.querySelectorAll(".tile").length===12');
  await run('document.querySelectorAll(".tile .actions button")[1].click()');await until('document.querySelector("#dialog-body .row")');await run('document.querySelector("#dialog-body .row").click()');await until('document.getElementById("dialog").style.display==="none"');
  await run('document.querySelector(".tile .open").click()');await until('document.getElementById("photo").naturalWidth>0 && document.getElementById("clock").textContent==="1 / 15"');
  for(let i=0;i<12;i++)await click('photo-next');await until('document.getElementById("clock").textContent==="13 / 15"');await click('photo-prev');await until('document.getElementById("clock").textContent==="12 / 15"');
  await key(27);await until('document.getElementById("viewer").style.display==="none"');
  await run('document.querySelector("[data-view=video]").click()');await until('document.querySelectorAll(".tile").length===1');await run('document.querySelector(".tile .open").click()');await until('document.getElementById("video").videoWidth>0 && document.getElementById("video").currentTime>1');
  await click('pause');await until('document.getElementById("pause").textContent.includes("Retomar")');await click('pause');await until('document.getElementById("video").currentTime>1');await click('forward');await until('document.getElementById("clock").textContent.match(/0:00:1[2-9]/)');
  await run('window.MagTV.ended()');await until('document.getElementById("viewer").style.display==="none"');
  const result=await(await fetch(fixture.url+'/api/personal?kind=video')).json();assert.equal(result.items[0].completed,1,'End must persist completed');
  const status=await(await fetch(fixture.url+'/api/personal?operation=status')).json();assert.equal(status.counts.photo,15);
  console.log('PASS web: favorites, shared albums, 15-photo pagination, fullscreen/back, real synthetic HLS playback, pause/resume/seek and completion.');
  await browse('web',390,844);await click('search-keyboard');assert.ok(await run('document.querySelector(".panel").getBoundingClientRect().right<=innerWidth'));await key(27);await run('document.getElementById("search").value="Fotografia 14";document.getElementById("search").dispatchEvent(new Event("input"))');await until('document.querySelectorAll(".tile").length===1');
  console.log('PASS mobile width: no overflow, onscreen search and live filtering.');
  await browse('mag',1280,720);await key(39);assert.equal(await run('document.activeElement.getAttribute("data-view")'),'photo');await key(13);await until('document.getElementById("heading").textContent==="Fotografias"');await click('new-album');assert.equal(await run('document.activeElement.textContent'),'A');await key(39);await key(13);assert.equal(await run('document.querySelector("#dialog-body input").value'),'B');await key(27);
  await browse('tv',1280,720);await run('window.MagTV.remote(39)');assert.equal(await run('document.activeElement.getAttribute("data-view")'),'photo');await run('window.MagTV.remote(13)');await until('document.getElementById("heading").textContent==="Fotografias"');await run('document.querySelector("[data-view=favorites]").click()');await until('document.querySelectorAll(".tile").length===1');assert.ok(await run('document.querySelector(".tile .actions button").textContent.includes("★")'));
  console.log('PASS shared MAG/TV page: remote focus/arrows/OK/back, onscreen keyboard and favorites shared with web. Hardware playback remains untested.');
  assert.deepEqual(errors,[]);const shot=await call('Page.captureScreenshot');fs.writeFileSync(process.argv[3]+'/personal.png',Buffer.from(shot.data,'base64'));
 }finally{await call('Browser.close');w.close()}
})().catch(e=>{console.error(e.message);process.exit(1)});
