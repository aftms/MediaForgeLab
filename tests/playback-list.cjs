const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const source=fs.readFileSync('public/web/app.js','utf8'),part=source.slice(source.indexOf('/* The player browses'),source.indexOf('const trackControls='));
const nodes={},played=[],requests=[];let response;
const item=n=>({id:'m'+n,name:'Movie '+n,kind:'movie'});
const ctx={rows:[item(0),item(1)],offset:0,total:5,section:'movie',state:{kind:'movie',view:'items',country:'PT',origin:'MEO',group:'Desporto',q:'abc'},starting:false,playingItem:item(1),pageSize:()=>2,Option:function(name,value){this.text=name;this.value=value},$:id=>nodes[id]||(nodes[id]={value:'',replaceChildren(){},add(){}}),text(){},query:o=>new URLSearchParams(o).toString(),api:async path=>{requests.push(path);return typeof response==='function'?response():response},play:async item=>{played.push(item.id);ctx.playingItem=item}};
vm.createContext(ctx);vm.runInContext(part,ctx);const run=s=>vm.runInContext(s,ctx);
(async()=>{
 run('capturePlaybackList(playingItem);renderPlaybackList()');ctx.state.group='changed';response={offset:2,total:5,items:[item(2),item(3)]};await run('adjacentPlayback(1)');assert.equal(played.at(-1),'m2');assert.ok(requests.at(-1).includes('group=Desporto'));assert.ok(requests.at(-1).includes('origin=MEO'));assert.ok(requests.at(-1).includes('q=abc'));
 await run('adjacentPlayback(1)');assert.equal(played.at(-1),'m3');const before=played.length;nodes['play-list'].value='page:next';response={offset:4,total:5,items:[item(4)]};await run('choosePlayback()');assert.equal(played.length,before,'Browsing pages must not start media');assert.equal(run('playbackList.index'),3);
 nodes['play-list'].value='0';await run('choosePlayback()');assert.equal(played.at(-1),'m4');run('renderPlaybackList()');assert.equal(nodes['play-next'].disabled,true);
 run('selectionBusy=true');await run('adjacentPlayback(-1)');assert.equal(played.at(-1),'m4');run('selectionBusy=false');
 response=()=>Promise.reject(Error('fixture error'));await run('adjacentPlayback(-1)');assert.equal(played.at(-1),'m4');assert.equal(run('playbackList.loading'),false);
 let finish;response=()=>new Promise(r=>finish=r);const pending=run('fetchPlaybackPage(0)');run('closePlaybackList()');finish({items:[item(0)],offset:0,total:1});assert.equal(await pending,false);assert.equal(run('playbackList'),null);
 ctx.section='favorites';ctx.state={kind:'movie',view:'items',folder:'my-folder',quality:'HD'};ctx.playingItem=item(1);run('capturePlaybackList(playingItem)');response={items:[item(2)],offset:2,total:3};await run('adjacentPlayback(1)');assert.ok(requests.at(-1).startsWith('/api/favorites?'));assert.ok(requests.at(-1).includes('folder=my-folder'));
 console.log('PASS active playback list: frozen filters/order, cross-page next, selector paging without play, direct pick, boundaries, busy guard, failure keeps selection, close discards stale results, favorites folder.');
})().catch(e=>{console.error(e);process.exit(1)});
