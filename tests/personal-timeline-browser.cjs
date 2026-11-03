const fs=require('fs'),assert=require('assert/strict'),sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 const fixture=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),port=fs.readFileSync(process.argv[3]+'/DevToolsActivePort','utf8').split('\n')[0];
 const tabs=await(await fetch('http://127.0.0.1:'+port+'/json')).json(),w=new WebSocket(tabs.find(t=>t.type==='page').webSocketDebuggerUrl);await new Promise(r=>w.onopen=r);
 let id=0;const pending=new Map(),errors=[];w.onmessage=e=>{const d=JSON.parse(e.data);if(d.method==='Runtime.exceptionThrown')errors.push(d.params.exceptionDetails.text);if(d.id&&pending.has(d.id)){const p=pending.get(d.id);pending.delete(d.id);d.error?p.reject(Error(d.error.message)):p.resolve(d.result)}};
 const call=(method,params={})=>new Promise((resolve,reject)=>{pending.set(++id,{resolve,reject});w.send(JSON.stringify({id,method,params}))});
 async function run(expression){const r=await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;}
 async function until(expr){for(let i=0;i<350;i++){if(await run(expr))return;await sleep(100)}throw Error('Timeout '+expr+' '+JSON.stringify(await run('({status:document.getElementById("view-status").textContent,disabled:document.getElementById("seek-position").disabled,paused:document.getElementById("video").paused,ready:document.getElementById("video").readyState,time:document.getElementById("video").currentTime,error:document.getElementById("video").error&&document.getElementById("video").error.code,requests:window.playRequests})')))}
 const click=id=>run('document.getElementById('+JSON.stringify(id)+').click()');
 async function key(k){await call('Input.dispatchKeyEvent',{type:'keyDown',windowsVirtualKeyCode:k});await call('Input.dispatchKeyEvent',{type:'keyUp',windowsVirtualKeyCode:k});}
 async function browse(client,width,height){await call('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false});await call('Page.navigate',{url:fixture.url+(client==='web'?'/web/personal/':'/tv/personal.html')+'?client='+client});await until("document.getElementById('page-size')&&typeof document.getElementById('page-size').onchange==='function'");await run("document.getElementById('page-size').value='12';document.getElementById('page-size').onchange()");await until('document.querySelectorAll(".tile").length===12');assert.ok(await run('document.documentElement.scrollWidth<=innerWidth'));}

 try{
  await call('Page.enable');await call('Runtime.enable');await browse('web',1280,720);
  await run(`window.playRequests=[];const send=XMLHttpRequest.prototype.send;XMLHttpRequest.prototype.send=function(body){if(typeof body==='string'){try{const d=JSON.parse(body);if(d.operation==='play')window.playRequests.push(d.position)}catch(e){}}return send.apply(this,arguments)}`);
  await run('document.querySelector("[data-view=video]").click()');await until('document.querySelectorAll(".tile").length===1');await run('document.querySelector(".tile .open").click()');
  assert.ok(await run('document.getElementById("seek-position").disabled'));
  await until('document.getElementById("video").currentTime>1 && !document.getElementById("seek-position").disabled');
  await click('pause');await until('document.getElementById("pause").textContent.includes("Retomar")');
  let before=await run('playRequests.length');
  await run('var slider=document.getElementById("seek-position");slider.focus();slider.value=8;slider.dispatchEvent(new Event("input"));slider.dispatchEvent(new Event("change"))');
  await sleep(600);assert.equal(await run('playRequests.length'),before);assert.ok(await run('document.getElementById("view-status").textContent.includes("Em pausa")'));
  await click('pause');await until('document.getElementById("video").currentTime>0.3 && !document.getElementById("seek-position").disabled');assert.equal(await run('playRequests[playRequests.length-1]'),8);
  before=await run('playRequests.length');
  await run('var slider=document.getElementById("seek-position");slider.focus();[2,3,4].forEach(n=>{slider.value=n;slider.dispatchEvent(new Event("input"))})');
  await sleep(1100);assert.equal(await run('playRequests.length'),before);assert.equal(await run('Number(document.getElementById("seek-position").value)'),4);
  await run('slider.dispatchEvent(new Event("change"));slider.dispatchEvent(new Event("mouseup"))');
  await until('playRequests.length==='+String(before+1));await until('document.getElementById("video").currentTime>0.3 && !document.getElementById("seek-position").disabled');assert.equal(await run('playRequests.length'),before+1);assert.equal(await run('playRequests[playRequests.length-1]'),4);
  before=await run('playRequests.length');await run('slider.focus();MagTV.remote(39);MagTV.back()');await sleep(600);assert.equal(await run('playRequests.length'),before);assert.equal(await run('document.getElementById("viewer").style.display'),'block');
  await run('slider.focus();MagTV.remote(39)');const target=await run('Number(slider.value)');await run('MagTV.remote(13)');await until('playRequests.length==='+String(before+1));await until('document.getElementById("video").currentTime>0.3 && !document.getElementById("seek-position").disabled');assert.equal(await run('playRequests[playRequests.length-1]'),target);
  assert.ok(await run('document.getElementById("video").videoWidth>0 && !document.getElementById("video").error'));
  await run('slider.focus()');const shot=await call('Page.captureScreenshot');fs.writeFileSync(process.argv[3]+'/timeline-desktop.png',Buffer.from(shot.data,'base64'));
  await call('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:false});assert.ok(await run('document.documentElement.scrollWidth<=innerWidth && document.getElementById("seek-position").getBoundingClientRect().right<=innerWidth'));
  const mobile=await call('Page.captureScreenshot');fs.writeFileSync(process.argv[3]+'/timeline-mobile.png',Buffer.from(mobile.data,'base64'));
  await click('close-viewer');await until('document.getElementById("viewer").style.display==="none"');
  const status=await(await fetch(fixture.url+'/api/personal?operation=status')).json();assert.equal(status.playback.active,false);
  assert.deepEqual(errors,[]);console.log('PASS Chrome synthetic video: paused seek stays paused, drag only commits once, remote arrows/OK/BACK, playback after seek, mobile fit, session released.');
 }finally{await run('if(window.MagTV)MagTV.suspend()');await call('Browser.close');w.close()}
})().catch(e=>{console.error(e.message);process.exit(1)});
