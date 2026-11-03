const assert=require('assert/strict'),fs=require('fs'),vm=require('vm');
const source=fs.readFileSync('public/tv/personal.js','utf8');
const code=source.slice(source.indexOf('function seekTo('),source.indexOf('function bar('));
function setup(){
 const elements={'seek-position':{value:0,max:0,disabled:false,setAttribute(k,v){this[k]=v}},'seek-label':{},'view-status':{}},starts=[],saves=[],timers=new Map();let next=0;
 const c={active:{kind:'video'},starting:false,duration:100,paused:null,seekPreview:null,scrubbing:false,seekTimer:null,position:()=>c.paused===null?5:c.paused,$:id=>elements[id],text:(n,t)=>n.textContent=t,format:v=>String(Math.floor(v)),save:()=>saves.push(c.position()),start:p=>starts.push(p),bar(){},move(){},setTimeout:f=>{timers.set(++next,f);return next},clearTimeout:id=>timers.delete(id)};
 vm.createContext(c);vm.runInContext(code,c);return {c,e:elements,starts,saves,timers,flush(){for(const [id,f] of [...timers]){timers.delete(id);f()}}};
}
const s=setup();s.c.updateTimeline(5);assert.equal(s.e['seek-position'].value,5);
s.c.previewTimeline(5.94);assert.equal(s.c.seekPreview,6);s.c.previewTimeline(40);s.c.previewTimeline(42);s.c.updateTimeline(7);assert.equal(s.e['seek-position'].value,42);assert.equal(s.saves.length,0);assert.equal(s.starts.length,0);
s.c.commitTimeline();s.c.commitTimeline();assert.equal(s.timers.size,1);s.flush();assert.deepEqual(s.starts,[42]);
const cancel=setup();cancel.c.updateTimeline(5);cancel.c.timelineKey(39);assert.equal(cancel.c.seekPreview,6);assert.equal(cancel.c.timelineKey(27),true);assert.equal(cancel.c.seekPreview,null);assert.equal(cancel.starts.length,0);
const paused=setup();paused.c.paused=20;paused.c.updateTimeline(20);paused.c.previewTimeline(70);paused.c.timelineKey(13);assert.equal(paused.c.paused,70);assert.deepEqual(paused.saves,[70]);assert.equal(paused.starts.length,0);
const bounded=setup();bounded.c.updateTimeline(5);bounded.c.previewTimeline(500);assert.equal(bounded.c.seekPreview,99);bounded.c.previewTimeline(-10);assert.equal(bounded.c.seekPreview,0);bounded.c.starting=true;bounded.c.updateTimeline(0);bounded.c.previewTimeline(10);assert.equal(bounded.c.seekPreview,0);assert.equal(bounded.e['seek-position'].disabled,true);
const unknown=setup();unknown.c.duration=0;unknown.c.updateTimeline(0);unknown.c.previewTimeline(20);assert.equal(unknown.e['seek-position'].disabled,true);assert.equal(unknown.c.seekPreview,null);
console.log('PASS personal timeline: drag previews without requests, one commit, range bounds, remote confirm/cancel, paused position and disabled unknown/preparing duration.');
