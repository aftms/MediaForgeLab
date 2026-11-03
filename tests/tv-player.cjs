const assert=require('assert/strict'),fs=require('fs'),vm=require('vm');
let state='IDLE',closed=0,prepared,played=0;
const av={stop(){if(state==='IDLE')throw Error('InvalidState');state='IDLE';},close(){closed++;state='NONE';},open(){assert.equal(state,'NONE');state='IDLE';},setDisplayRect(){},setDisplayMethod(){},setListener(){},prepareAsync(fn){prepared=fn;},play(){played++;state='PLAYING';},getState(){return state;}};
const video={pause(){},removeAttribute(){},load(){}};
const context={window:{webapis:{avplay:av}},document:{getElementById(){return video;}},setTimeout(){return 1;},clearTimeout(){}};
vm.runInNewContext(fs.readFileSync(require('path').join(__dirname,'../public/tv/player.js'),'utf8'),context);
const player=context.window.TVPlayer;
player.stop();assert.equal(state,'NONE');assert.equal(closed,1);
player.open('http://fixture.invalid/local.m3u8',()=>{});assert.equal(state,'IDLE');const stale=prepared;
player.stop();assert.equal(state,'NONE');stale();assert.equal(played,0);
player.open('http://fixture.invalid/local.m3u8',()=>{});prepared();assert.equal(state,'PLAYING');player.stop();assert.equal(state,'NONE');
console.log('PASS: Samsung closes after IDLE stop rejection, resets before open and ignores stale preparation callbacks.');

// The early Collections shell must not attach to Pessoal or the normal TV page.
{const env={window:{},location:{search:'?client=mag'},document:{getElementById:function(){return null;}}};vm.runInNewContext(fs.readFileSync(require('path').join(__dirname,'../public/tv/player.js'),'utf8'),env);assert.equal(env.window.MFLCollectionShell,undefined);console.log('PASS: independent Collections boot guard stays out of other MAG modules.');}
