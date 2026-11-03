const assert=require('assert/strict'),fs=require('fs'),vm=require('vm');
const source=fs.readFileSync(require('path').join(__dirname,'../public/web/app.js'),'utf8');
const nodes=new Map(),requests=[];let nextStart,progressGate,phase='analysis';
const context={updateVideoControls(){},showVideoControls(){},renderPlaybackList(){},trackControls:{prepare(){},reset(){},feed(){},update(){}},Hls:{},setTimeout(){return 1;},clearTimeout(){},console,Option:function(){},
 $:id=>{if(!nodes.has(id))nodes.set(id,{value:0,textContent:'',disabled:false,setAttribute(){},replaceChildren(){},add(){}});return nodes.get(id)},
 api:async(path,data)=>{requests.push({path,data});if(path==='/api/progress')return progressGate||{};if(path==='/api/media/web')return nextStart;if(path==='/api/media/pulse')return {token:'test',state:'preparing',stage:phase,duration:phase==='remux'?1200:0};return {};},
 document:{activeElement:null}};
context.text=(id,value)=>context.$(id).textContent=value;
vm.createContext(context);
vm.runInContext(`let session=null,playingItem={id:'m1',kind:'movie'},hls=null,basePosition=600,duration=1200,lastSaved=0,starting=false,playerGeneration=0,audioIndex=0,subtitleIndex=-1,compatibility=false,pausedPosition=null,pollTimer,pauseTimer=null,pauseEpoch=0,seekBusy=false,seekingTimeline=false,playbackStarted=false;
const owner='test-owner';const video={currentTime:600,pause(){},removeAttribute(){},load(){}};
function fmt(t){return Math.floor(t/60).toString().padStart(2,'0')+':'+Math.floor(t%60).toString().padStart(2,'0');}
`+source.slice(source.indexOf('function updateTime()'),source.indexOf('async function refreshStatus()')),context);
const run=code=>vm.runInContext(code,context);
(async()=>{
 let resolve;nextStart=new Promise(r=>resolve=r);const pending=run('start(8)');
 await Promise.resolve();assert.equal(context.$('play-time').textContent,'00:08 / —');assert.equal(context.$('timeline').value,0);assert.equal(context.$('timeline').disabled,true);assert.equal(context.$('forward').disabled,true);
 run('updateTime()');assert.equal(context.$('play-time').textContent,'00:08 / —');
 resolve({token:'test',position:8,duration:0,stage:'analysis'});await pending;
 assert.match(context.$('play-status').textContent,/formato/);
 phase='remux';await run('ready(playerGeneration)');assert.equal(context.$('play-time').textContent,'00:08 / 20:00');assert.equal(context.$('timeline').disabled,true);
 await run('stop()');assert.equal(requests.filter(r=>r.path==='/api/progress').length,0,'Preparation must not overwrite saved progress');assert.equal(requests.filter(r=>r.path==='/api/media/stop').length,1);
 let reject;nextStart=new Promise((_,r)=>reject=r);const cancelled=run('start(0)');await Promise.resolve();await run('stop()');context.text('play-status','closed');reject(Error('late error'));await cancelled;assert.equal(context.$('play-status').textContent,'closed');
 nextStart=new Promise(r=>resolve=r);const delayed=run('start(0)');await Promise.resolve();await run('stop()');resolve({token:'late',position:0});await delayed;assert.equal(requests.filter(r=>r.path==='/api/media/stop'&&r.data.token==='late').length,1);
 // Paused positioning is local until resume, and late progress cannot reopen a closed player.
 run('session=null;starting=false;pausedPosition=120;duration=900;video.paused=true');
 const oldRequests=requests.length;await run('seek(400)');assert.equal(run('pausedPosition'),400);assert.ok(requests.slice(oldRequests).every(r=>r.path==="/api/progress"),"Paused seek only saves progress, never opens stream");assert.equal(context.$('timeline').value,400);await run('stop()');assert.equal(requests.at(-1).path,'/api/progress');assert.equal(requests.at(-1).data.position,400);
 run('session={token:"seek-test"};pausedPosition=null;video.paused=false;video.currentTime=20');
 let releaseProgress;progressGate=new Promise(r=>releaseProgress=r);
 const startsBefore=requests.filter(r=>r.path==='/api/media/web').length,waitingSeek=run('seek(500)');await Promise.resolve();
 const duplicate=run('seek(600)');await duplicate;assert.equal(run('seekBusy'),true);
 const closing=run('stop()');await Promise.resolve();releaseProgress({});await Promise.all([waitingSeek,closing]);progressGate=null;
 assert.equal(requests.filter(r=>r.path==='/api/media/web').length,startsBefore,'Cancelled seek must not reopen');
 assert.equal(run('seekBusy'),false);
 console.log('PASS paused seek opens no stream, duplicate seek ignored, close cancels delayed seek.');
 console.log('PASS: web preparation resets unknown duration, disables seeking, shows phases, preserves progress and releases late/cancelled sessions.');
})().catch(e=>{console.error(e);process.exit(1)});
