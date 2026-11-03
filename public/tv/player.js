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
