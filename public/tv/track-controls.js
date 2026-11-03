/* ES5 shared language controls. No upstream URLs, HTML injection or extra streams. */
(function(){'use strict';
var languages={por:'Português',pt:'Português',eng:'Inglês',en:'Inglês',spa:'Espanhol',es:'Espanhol',fra:'Francês',fre:'Francês',fr:'Francês',deu:'Alemão',ger:'Alemão',de:'Alemão',ita:'Italiano',it:'Italiano',jpn:'Japonês',ja:'Japonês',und:'Idioma não indicado'};
function label(t,kind){var lang=String(t.language||'').toLowerCase(),name=languages[lang]||t.language||kind+' '+(t.index+1);return name+(t.title?' · '+t.title:'')+(t.supported===false?' · formato ainda não suportado':'');}
window.MediaTrackControls=function(root,video,position,changed,overlayParent){
 var self=this,audio=0,subtitle=-1,cues=[],timer=null,nativeTrack=null,known={},overlay=document.createElement('div');overlay.className='media-captions';overlayParent.appendChild(overlay);
 root.className+=' media-track-controls';var title=document.createElement('button'),body=document.createElement('div'),opened=false;title.type='button';title.textContent='Áudio e legendas';title.setAttribute('aria-expanded',String(opened));root.appendChild(title);root.appendChild(body);body.style.display=opened?'block':'none';title.onclick=function(){opened=!opened;body.style.display=opened?'block':'none';title.setAttribute('aria-expanded',String(opened));};
 function select(name){var wrap=document.createElement('label'),text=document.createElement('span'),field=document.createElement('select');text.textContent=name;field.setAttribute('aria-label',name);wrap.appendChild(text);wrap.appendChild(field);body.appendChild(wrap);return field;}
 var a=select('Áudio'),s=select('Legendas'),note=document.createElement('small');body.appendChild(note);note.setAttribute('role','status');
 if(video&&video.addTextTrack&&window.VTTCue){try{nativeTrack=video.addTextTrack('subtitles','Media Forge Lab');nativeTrack.mode='showing';}catch(ignore){}}
 function clear(){cues=[];known={};overlay.textContent='';if(nativeTrack){nativeTrack.mode='hidden';while(nativeTrack.cues&&nativeTrack.cues.length)nativeTrack.removeCue(nativeTrack.cues[0]);nativeTrack.mode=subtitle<0?'disabled':'hidden';}}
 function tick(){var now=position();if(nativeTrack){nativeTrack.mode=subtitle<0?'disabled':'showing';return;}var bar=overlayParent.querySelector('#viewer-bar,#player-bar');if(bar)overlay.style.bottom=bar.className.indexOf('quiet')>=0?'8%':Math.min(70,bar.offsetHeight/window.innerHeight*100+4)+'%';var lines=[];for(var i=0;i<cues.length;i++)if(cues[i].start<=now&&cues[i].end>now)lines.push(cues[i].text);overlay.textContent=subtitle<0?'':lines.join('\n');}
 function options(field,tracks,empty,kind,selected,off){field.innerHTML='';if(off)field.add(new Option('Desligadas',-1));for(var i=0;i<tracks.length;i++){var t=tracks[i],opt=new Option(label(t,kind),t.index);opt.disabled=t.supported===false;field.add(opt);}if(!field.options.length)field.add(new Option(empty,0));field.value=selected;}
 this.clear=function(){clear();clearInterval(timer);timer=null;};
 this.values=function(){return {audio:audio,subtitle:subtitle};};
 this.reset=function(){opened=false;body.style.display='none';title.setAttribute('aria-expanded','false');audio=0;subtitle=-1;clear();clearInterval(timer);timer=null;};
 this.prepare=function(){clear();a.disabled=s.disabled=true;note.textContent='A verificar as faixas disponíveis…';};
 this.update=function(data){audio=Number(data.audio_index)||0;subtitle=data.subtitle_index===undefined?-1:Number(data.subtitle_index);var at=data.audio||[],st=data.subtitles||[],supported=0;for(var i=0;i<st.length;i++)if(st[i].supported!==false)supported++;
 options(a,at,data.tracks_known===false?'Automático':'Sem faixa detetada','Áudio',audio,false);options(s,st,'','Legenda',subtitle,true);a.disabled=at.length<2;s.disabled=!supported;
 note.textContent=data.tracks_known===false?'Faixas ainda não analisadas. Use Compatibilidade para as verificar.':(at.length===1?'Uma faixa de áudio. ':at.length===0?'Sem áudio detetado. ':'')+(st.length===0?'Sem legendas selecionáveis neste vídeo.':!supported?'As legendas disponíveis usam um formato ainda não suportado.':'Alterar a faixa prepara novamente o vídeo na posição atual.');
 self.feed(data);if(!timer)timer=setInterval(tick,200);
 };
 this.feed=function(data){if(subtitle<0){clear();return;}cues=data.cues||cues;if(nativeTrack){nativeTrack.mode='showing';var now=position();for(var j=nativeTrack.cues.length-1;j>=0;j--){var old=nativeTrack.cues[j];if(old.endTime<now-15){delete known[old.id];nativeTrack.removeCue(old);}}for(var i=0;i<cues.length;i++){var c=cues[i],key=c.start+'|'+c.end+'|'+c.text;if(c.end<now-15||known[key])continue;var cue=new VTTCue(c.start,c.end,c.text);cue.id=key;nativeTrack.addCue(cue);known[key]=true;}}tick();};
 a.onchange=s.onchange=function(){audio=Number(a.value)||0;subtitle=Number(s.value);clear();changed(audio,subtitle);};
 this.handleKey=function(code,el,repeat){if((el!==a&&el!==s)||el.disabled)return false;var editing=el.getAttribute('data-track-edit');if(code===13||code===65376){if(repeat)return true;if(editing!==null){el.removeAttribute('data-track-edit');el.onchange();}else el.setAttribute('data-track-edit',el.value);return true;}if(editing===null)return false;if(code===27||code===10009||code===461||code===8){el.value=editing;el.removeAttribute('data-track-edit');return true;}if(code>=37&&code<=40){var step=code===37||code===38?-1:1,i=el.selectedIndex+step;while(i>=0&&i<el.options.length){if(!el.options[i].disabled){el.selectedIndex=i;break;}i+=step;}return true;}return false;};
 this.reset();this.prepare();
};
}());
