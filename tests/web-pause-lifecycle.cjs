const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const source=fs.readFileSync(require('path').join(__dirname,'../public/web/app.js'),'utf8');
const timers=new Map(),requests=[],messages=[];let nextTimer=0,saves=0,progressGate;
const ctx={setTimeout(fn){timers.set(++nextTimer,fn);return nextTimer},clearTimeout(id){timers.delete(id)},saveProgress:async()=>{saves++;await progressGate},api:async(path,data)=>requests.push({path,data}),text:(id,value)=>messages.push(value),updateVideoControls(){}};
vm.createContext(ctx);vm.runInContext(`let starting=false,session={token:'first'},playerGeneration=1,pauseEpoch=0,pauseTimer=null,pausedPosition=null,pollTimer=null,basePosition=90,playbackStarted=false;const video={paused:true,ended:false,currentTime:0,play:async()=>{}};const hls={stopLoad(){}};`+source.slice(source.indexOf('function cancelPauseRelease()'),source.indexOf('async function saveProgress()'))+source.slice(source.indexOf('async function attemptPlayback('),source.indexOf('async function ready('))+source.split('\n').find(line=>line.startsWith('video.onplaying=')),ctx);
const run=s=>vm.runInContext(s,ctx);async function flush(){for(const [id,fn]of Array.from(timers)){timers.delete(id);await fn()}}
(async()=>{
 run('schedulePauseRelease()');await flush();assert.equal(requests.length,0);assert.equal(saves,0,'Startup must not overwrite saved position');
 await run('attemptPlayback(1)');assert.equal(run('playbackStarted'),false,'play promise alone is not proof of playback');
 run('video.onplaying();video.paused=true;schedulePauseRelease()');await flush();assert.equal(requests.length,1);assert.equal(run('pausedPosition'),90);assert.match(messages.at(-1),/Em pausa/);
 run('session={token:"second"};pausedPosition=null;playbackStarted=true;video.paused=true;schedulePauseRelease();video.paused=false;cancelPauseRelease()');await flush();assert.equal(requests.length,1,'Transient pause stays connected');
 let release;progressGate=new Promise(r=>release=r);run('video.paused=true;schedulePauseRelease()');const waiting=flush();await Promise.resolve();run('playerGeneration++;session={token:"replacement"}');release();await waiting;progressGate=null;assert.equal(requests.length,1,'Late pause cannot stop replacement');
 run('basePosition=123;playbackStarted=false;video.play=async()=>{const e=new Error("blocked");e.name="NotAllowedError";throw e}');const beforeSaves=saves;await run('attemptPlayback(playerGeneration)');assert.equal(requests.length,2);assert.equal(run('pausedPosition'),123);assert.equal(saves,beforeSaves);assert.match(messages.at(-1),/navegador bloqueou/);assert.doesNotMatch(messages.at(-1),/Em pausa/);
 let reject;ctx.pendingPlay=new Promise((_,r)=>reject=r);run('session={token:"old"};video.play=()=>pendingPlay');const late=run('attemptPlayback(playerGeneration)');run('playerGeneration++;session={token:"new"}');reject(Error('late'));await late;assert.equal(requests.length,2);
 console.log('PASS startup pause ignored, playing arms real pause, transient pause preserved, late pause/start discarded, autoplay denial releases with accurate message and preserves position.');
})().catch(e=>{console.error(e);process.exit(1)});
