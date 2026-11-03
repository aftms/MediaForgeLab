/* Keep MAG exit independent of library startup, HTTP and optional helpers. */
(function(){
 if(typeof location==='undefined'||!/client=mag/.test(location.search)||!document.getElementById('play-sequence'))return;
 var shell={handle:null};document.body.className='mag';
 function cancel(e){if(e.preventDefault)e.preventDefault();e.returnValue=false;return false;}
 shell.home=function(){try{var player=window.gSTB||window.stb;if(player)player.Stop();}catch(ignore){}location.href='/';return false;};
 shell.fail=function(){var node=document.getElementById('status');if(node)node.textContent='Não foi possível concluir esta operação. Prima Voltar para regressar à biblioteca.';};
 var home=document.getElementById('home');if(home)home.onclick=shell.home;
 try{var player=window.gSTB||window.stb;if(player&&player.EnableSpatialNavigation)player.EnableSpatialNavigation(false);}catch(ignore){}
 document.onkeydown=function(event){var e=event||window.event||{},key=e.keyCode||e.which;
  /* MENU always leaves the module, including when an embedded player has failed. */
  if(key===122){cancel(e);return shell.home();}
  try{if(shell.handle)return shell.handle(e);}catch(ignore){shell.fail();if(key===8||key===27||key===10009||key===461){cancel(e);return shell.home();}return cancel(e);}
  if(key===8||key===27||key===10009||key===461||key===13&&document.activeElement===home){cancel(e);return shell.home();}
 };
 window.MFLCollectionShell=shell;setTimeout(function(){if(!shell.handle)shell.fail();},8000);
}());
/* ES5 adapters. Supplier addresses never reach a TV. */
(function(){'use strict';var av=null,video,hls=null,generation=0,position=0,timer;
function nativePlayer(){return window.MagPlayer||null;}
window.TVPlayer={
 open:function(url,notify){var stamp=++generation;video=document.getElementById('video');position=0;
  if(nativePlayer()){video.hidden=true;nativePlayer().play(url);return;}
  av=window.webapis&&window.webapis.avplay;
  if(av){video.hidden=true;try{try{av.stop();}catch(ignored){}try{av.close();}catch(ignored){}av.open(url);av.setDisplayRect(0,0,1920,1080);av.setDisplayMethod('PLAYER_DISPLAY_MODE_LETTER_BOX');av.setListener({oncurrentplaytime:function(ms){position=ms/1000;},onerror:function(){if(stamp===generation)notify('Não foi possível reproduzir. Volte à biblioteca ou tente Compatibilidade.');},onstreamcompleted:function(){if(window.MagTV)window.MagTV.ended();}});timer=setTimeout(function(){if(stamp===generation&&av.getState()!=='PLAYING')notify('O leitor demorou demasiado. Volte à biblioteca ou tente Compatibilidade.');},20000);av.prepareAsync(function(){if(stamp===generation){av.play();}},function(){if(stamp===generation)notify('A TV não conseguiu preparar o vídeo. Tente Compatibilidade.');});}catch(e){notify('O leitor Samsung recusou este formato. Tente Compatibilidade.');}return;}
  video.hidden=false;video.src=url;video.play().catch(function(){notify('Prima OK em Retomar para iniciar.');});
 },
 stop:function(){++generation;clearTimeout(timer);try{if(nativePlayer())nativePlayer().stop();av=av||(window.webapis&&window.webapis.avplay);if(av){try{av.stop();}catch(ignored){}try{av.close();}catch(ignored){}}if(video){video.pause();video.removeAttribute('src');video.load();}}catch(e){}position=0;},
 position:function(){if(nativePlayer())return Number(nativePlayer().position())||0;return av?position:(video?video.currentTime||0:0);}
};
if(typeof tizen!=='undefined'){try{['MediaPlay','MediaPause','MediaPlayPause','MediaStop','MediaFastForward','MediaRewind','ChannelUp','ChannelDown'].forEach(function(k){try{tizen.tvinputdevice.registerKey(k);}catch(e){}});}catch(e){}}
}());
