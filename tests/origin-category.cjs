const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
for(const type of ['web','tv']){
 const source=fs.readFileSync(type==='web'?'public/web/app.js':'public/tv/tv.js','utf8'),nodes={},requests=[];let refreshes=0;
 const state={kind:'tv',country:'PT',origin:'VO',group:'Desporto'};
 const $=id=>nodes[id]||(nodes[id]={value:id==='category'||id==='group'?'Desporto':'',options:['Todas','Desporto','Filmes'],removeAttribute(){}});
 const context={$,state,offset:60,load(){requests.push({...state})},filters(){refreshes++},document:{},setTimeout(){},clearTimeout(){}};
 vm.createContext(context);
 const fragment=type==='web'?source.slice(source.indexOf("$('country').onchange="),source.indexOf("$('back').onclick=")):source.slice(source.indexOf("['country','origin','group'"),source.indexOf("$('search').oninput="));
 vm.runInContext(fragment,context);
 const category=$(type==='web'?'category':'group'),options=category.options;
 for(const value of ['MEO','MEO,VO','VO','']){$('origin').value=value;$('origin').onchange();assert.equal(state.group,'Desporto');assert.equal(category.value,'Desporto');assert.equal(category.options,options);assert.equal(refreshes,0);assert.equal(requests.at(-1).origin,value);assert.equal(requests.at(-1).group,'Desporto');assert.equal(context.offset,0);}
 $('country').value='ES';$('country').onchange();assert.equal(state.group,'');assert.equal(state.origin,'');assert.equal(refreshes,1);
 console.log('PASS '+type+': source changes and clearing preserve category/options; country change still resets dependent filters. No streams.');
}
