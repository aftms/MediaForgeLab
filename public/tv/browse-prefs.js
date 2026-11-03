/* ES5 browsing preferences only: never store credentials, URLs or playback leases. */
(function(){'use strict';
window.BrowsePrefs={create:function(scope,fields){
 var key='mfl-browse-v1:'+scope,data={version:1,slots:{},last:''};
 function clean(value){var result={},i,k,v;if(!value||typeof value!=='object')return result;for(i=0;i<fields.length;i++){k=fields[i];v=value[k];if(typeof v==='string'&&v.length<=400){if(k==='quality'&&['','auto','all','SD','HD','FHD','4K','8K','UNKNOWN'].indexOf(v)===-1)continue;if(k==='country'&&v&&!/^[A-Z]{2}$/.test(v))continue;if(k==='origin'&&v&&!/^[A-Z0-9_, -]+$/.test(v))continue;if(k==='view'&&['items','groups','countries'].indexOf(v)===-1)continue;if(k==='kind'&&['tv','movie','series','all','photo','video'].indexOf(v)===-1)continue;result[k]=v;}}return result;}
 try{var saved=JSON.parse(window.localStorage.getItem(key));if(saved&&saved.version===1&&saved.slots&&typeof saved.slots==='object'&&!Array.isArray(saved.slots)){data.last=typeof saved.last==='string'?saved.last:'';for(var slot in saved.slots)if(Object.prototype.hasOwnProperty.call(saved.slots,slot)&&/^[a-z:]{1,40}$/.test(slot))data.slots[slot]=clean(saved.slots[slot]);}}catch(ignore){}
 function write(slot,value){if(!/^[a-z:]{1,40}$/.test(slot))return;data.slots[slot]=clean(value);data.last=slot;try{window.localStorage.setItem(key,JSON.stringify(data));}catch(ignore){}}
 return {read:function(slot,defaults){var result=clean(defaults),saved=data.slots[slot]||{},k;for(k in saved)if(Object.prototype.hasOwnProperty.call(saved,k))result[k]=saved[k];return result;},write:write,last:function(fallback){return data.last||fallback;}};
}};
}());
