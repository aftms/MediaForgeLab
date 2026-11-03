const assert=require('assert/strict'),fs=require('fs'),vm=require('vm');
const source=fs.readFileSync('public/tv/personal.js','utf8');
const fn=source.slice(source.indexOf('function openWebVideo('),source.indexOf('function loadHls('));
function setup(mse,native){
 const errors=[],instances=[];let played=0;
 const video={canPlayType(){return native?'maybe':''},play(){played++;return {catch(){}}}};
 function Hls(config){this.config=config;this.events={};instances.push(this)}
 Hls.isSupported=()=>mse;Hls.Events={MANIFEST_PARSED:'manifest',ERROR:'error'};
 Hls.prototype.on=function(e,fn){this.events[e]=fn};Hls.prototype.loadSource=function(u){this.url=u};Hls.prototype.attachMedia=function(v){this.video=v};
 const c={window:{Hls},Hls,playSerial:4,active:{kind:'video'},hls:null,$:()=>video,loadHls:fn=>fn()};vm.createContext(c);vm.runInContext(fn,c);
 return {c,errors,instances,video,played:()=>played,open:()=>c.openWebVideo('http://local.invalid/test.m3u8',4,e=>errors.push(e))};
}
const both=setup(true,true);both.open();assert.equal(both.instances.length,1);assert.equal(both.video.src,undefined);both.instances[0].events.manifest();assert.equal(both.played(),1);both.instances[0].events.error(null,{fatal:true});assert.equal(both.errors.length,1);both.c.playSerial=5;both.instances[0].events.manifest();assert.equal(both.played(),1);
const fallback=setup(false,true);fallback.open();assert.equal(fallback.instances.length,0);assert.ok(fallback.video.src);assert.equal(fallback.played(),1);fallback.video.error={code:4};fallback.video.onerror();assert.equal(fallback.errors.length,1);
const unavailable=setup(false,false);unavailable.open();assert.equal(unavailable.errors.length,1);
const stale=setup(true,true);stale.c.playSerial=5;stale.open();assert.equal(stale.instances.length,0);
console.log('PASS personal web player: MSE preferred over native HLS; native fallback, explicit errors and cancelled-open protection.');
