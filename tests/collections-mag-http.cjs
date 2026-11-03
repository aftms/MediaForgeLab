const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const s=fs.readFileSync(require('path').join(__dirname,'../public/tv/collections.js'),'utf8');
const source=s.slice(s.indexOf('function request('),s.indexOf('function mutate('));
for(const mode of ['ok','invalid','null','error','timeout','retry','rejected']){
 let timer,requests=0,result,calls=0,last;
 function XHR(){this.readyState=0;this.status=0;last=this;}
 XHR.prototype.open=function(){};XHR.prototype.setRequestHeader=function(){};
 XHR.prototype.abort=function(){this.readyState=4;if(this.onreadystatechange)this.onreadystatechange();};
 XHR.prototype.send=function(){requests++;if(mode==='timeout')return;if(mode==='error'){this.onerror();return;}this.readyState=4;this.status=(mode==='retry'&&requests===1||mode==='rejected'&&requests!==2)?403:200;this.responseText=mode==='invalid'?'not-json':mode==='null'?'null':JSON.stringify(requests===2?{action_token:'refreshed'}:this.status===403?{error:'denied'}:{items:[]});this.onreadystatechange();if(this.onload)this.onload();};
 const env={XMLHttpRequest:XHR,base:'http://127.0.0.1',cfg:{},client:'mag',action:'original',setTimeout:fn=>{timer=fn;return 1;},clearTimeout:()=>{}};
 vm.createContext(env);vm.runInContext(source,env);env.done=(e,d)=>{calls++;result={e,d};};vm.runInContext(`api({},${['retry','rejected'].includes(mode)?'{operation:"favorite"}':'null'},done)`,env);
 if(mode==='timeout'){timer();last.readyState=4;last.status=200;last.responseText='{}';last.onreadystatechange();}
 assert.equal(calls,1,mode+' completes once');
 assert.equal(!!result.e,['invalid','null','error','timeout','rejected'].includes(mode),mode);
 if(mode==='retry'||mode==='rejected')assert.equal(requests,3,'One token refresh and one retry only');
}
console.log('PASS: legacy readyState completion, duplicate event suppression, malformed/error/deadline preservation, bounded 403 refresh.');
