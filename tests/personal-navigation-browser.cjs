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
 async function browse(client,width,height){await call('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false});await call('Page.navigate',{url:fixture.url+(client==='web'?'/web/personal/':'/tv/personal.html')+'?client='+client});await until('document.querySelectorAll(".tile").length===Math.min(16,Number(document.getElementById("page-size").value))');assert.ok(await run('document.documentElement.scrollWidth<=innerWidth'));}

 try{
 await call('Page.enable');await call('Runtime.enable');
 for(const [client,width,height] of [['mag',1280,720],['tv',1920,1080],['web',390,844]]){
  await browse(client,width,height);
  await run('document.querySelector(".tile .open").focus()');
  const idx=()=>run('Array.from(document.querySelectorAll(".tile .open")).indexOf(document.activeElement)');
  const cols=await run('Array.from(document.querySelectorAll(".tile .open")).filter(e=>Math.abs(e.getBoundingClientRect().top-document.querySelector(".tile .open").getBoundingClientRect().top)<10).length');
  await key(39);assert.equal(await idx(),1);await key(40);assert.equal(await idx(),1+cols);
  await key(37);assert.equal(await idx(),cols);await key(38);assert.equal(await idx(),0);
  assert.equal(await run('document.querySelectorAll(".tile.focused").length'),1);
  await key(38);assert.equal(await run('document.activeElement.id'),'item-options');
  await key(13);assert.equal(await run('document.getElementById("dialog-title").textContent'),'Opções do item');
  assert.ok(await run('document.activeElement.textContent.includes("favorito")'));
  await key(40);assert.ok(await run('document.activeElement.textContent.includes("álbum")'));await key(13);
  await key(27);assert.equal(await run('document.activeElement.id'),'item-options');
  const favoriteBefore=await run('document.querySelectorAll(".tile")[2].textContent.includes("★")');
  await run('document.querySelectorAll(".tile .open")[2].focus();MagTV.remote(73)');
  await key(13);await until('document.getElementById("dialog").style.display==="none" && document.querySelectorAll(".tile").length===Math.min(16,Number(document.getElementById("page-size").value))');await sleep(300);
  assert.equal(await idx(),2);assert.equal(await run('document.querySelectorAll(".tile")[2].textContent.includes("★")'),!favoriteBefore);
  const shot=await call('Page.captureScreenshot');fs.writeFileSync(process.argv[3]+'/personal-'+client+'.png',Buffer.from(shot.data,'base64'));
 }
 await call('Emulation.setDeviceMetricsOverride',{width:1280,height:720,deviceScaleFactor:1,mobile:false});
 await call('Page.navigate',{url:fixture.url+'/'});await until('!!document.getElementById("personal-button")');
 await sleep(400);await key(37);for(let i=0;i<4;i++)await key(40);
 await until('document.getElementById("personal-button").className.includes("remote-focus")');
 assert.equal(await run('document.getElementById("personal-button").parentNode.id'),'navigation');
 assert.ok(await run('document.getElementById("personal-button").getBoundingClientRect().bottom < document.getElementById("actions").getBoundingClientRect().top'));
 assert.equal(await run('getComputedStyle(document.getElementById("personal-button")).backgroundColor'),'rgb(55, 87, 92)');
 const shot=await call('Page.captureScreenshot');fs.writeFileSync(process.argv[3]+'/mag-menu.png',Buffer.from(shot.data,'base64'));
 assert.deepEqual(errors,[]);console.log('PASS personal grid: desktop/MAG/TV/mobile arrows skip actions, visible focus, options without colour keys, album dialog, favorite focus preservation; MAG main menu alignment/highlight. No provider streams.');
 }finally{await call('Browser.close');w.close()}
})().catch(e=>{console.error(e.message);process.exit(1)});
