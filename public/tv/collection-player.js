/* Isolated official embeds. No catalogue, supplier credentials or TV key here. */
(function(){'use strict';
var channel='',origin='',source=null,player=null,timer=null,started=false,serial=0,facebookFrame=null,facebookAspect=9/16;
function send(event,data){if(source)source.postMessage({source:'mfl-collections',channel:channel,event:event,data:data||{}},origin==='null'?'*':origin);}
function message(value){document.getElementById('message').textContent=value||'';}
function script(url,done){var s=document.createElement('script');s.src=url;s.onerror=function(){message('Não foi possível carregar este leitor.');send('error',{message:'Não foi possível carregar o leitor externo.'});};s.onload=done||function(){};document.head.appendChild(s);}
function fitFacebook(){if(!facebookFrame)return;var w=document.documentElement.clientWidth,h=document.documentElement.clientHeight;if(!w||!h)return;var width=720,height=Math.ceil(width/facebookAspect),scale=Math.min(w/width,h/height),left=(w-width*scale)/2,top=(h-height*scale)/2;facebookFrame.style.width=width+'px';facebookFrame.style.height=height+'px';facebookFrame.style.transformOrigin=facebookFrame.style.webkitTransformOrigin='0 0';facebookFrame.style.transform=facebookFrame.style.webkitTransform='translate('+left+'px,'+top+'px) scale('+scale+')';}
window.addEventListener('resize',fitFacebook,false);
function load(d){
 var stamp=++serial;started=false;message('A carregar vídeo…');
 if(d.platform==='youtube'&&/^[A-Za-z0-9_-]{11}$/.test(d.remote_id)){
  window.onYouTubeIframeAPIReady=function(){
   if(stamp!==serial)return;player=new YT.Player('host',{width:'100%',height:'100%',videoId:d.remote_id,playerVars:{playsinline:1,origin:location.protocol+'//'+location.host,start:Math.floor(d.position||0)},events:{
    onReady:function(e){send('ready',{controllable:true});if(d.muted)e.target.mute();if(!d.paused)e.target.playVideo();else send('paused');},
    onStateChange:function(e){if(stamp!==serial)return;if(e.data===1){started=true;message('');send('playing');}if(e.data===2)send('paused');if(e.data===0&&started){started=false;send('ended');}},
    onAutoplayBlocked:function(){message('Prima Retomar para iniciar o vídeo.');send('blocked',{message:'O navegador pede um toque em Retomar para iniciar.'});},
    onError:function(e){message('Vídeo indisponível neste leitor.');send('error',{message:'YouTube: vídeo indisponível ou reprodução integrada não permitida ('+e.data+'). Use Abrir na origem.'});}
   }});
   timer=setInterval(function(){try{if(started&&player&&player.getCurrentTime)send('time',{position:player.getCurrentTime(),duration:player.getDuration()});}catch(ignore){}},1000);
  };script('https://www.youtube.com/iframe_api');
 }else if(d.platform==='vimeo'&&/^\d+$/.test(d.remote_id)){
  script('https://player.vimeo.com/api/player.js',function(){if(stamp!==serial)return;player=new Vimeo.Player('host',{id:Number(d.remote_id),autoplay:false,muted:!!d.muted});player.ready().then(function(){send('ready',{controllable:true});return d.position?player.setCurrentTime(d.position):null;}).then(function(){return d.paused?null:player.play();}).catch(function(){send('blocked',{message:'Prima Retomar para iniciar.'});});player.on('play',function(){started=true;message('');send('playing');});player.on('pause',function(){send('paused');});player.on('ended',function(){if(started){started=false;send('ended');}});player.on('timeupdate',function(e){send('time',{position:e.seconds,duration:e.duration});});player.on('error',function(){send('error',{message:'Vimeo: reprodução indisponível. Use Abrir na origem.'});});});
 }else if(d.platform==='facebook'&&/^https:\/\/(www\.facebook\.com\/watch\/\?v=\d+|fb\.watch\/[A-Za-z0-9_-]+\/)$/.test(d.url)){
  facebookAspect=Number(d.aspect_ratio);if(!isFinite(facebookAspect)||facebookAspect<.2||facebookAspect>4)facebookAspect=9/16;document.documentElement.className='facebook';
  var frame=document.createElement('iframe');facebookFrame=frame;frame.title='Vídeo Facebook';frame.src='https://www.facebook.com/plugins/video.php?href='+encodeURIComponent(d.url)+'&show_text=false&autoplay=false&width=720&height='+Math.ceil(720/facebookAspect);frame.setAttribute('scrolling','no');frame.setAttribute('allow','autoplay; encrypted-media; fullscreen; picture-in-picture');frame.setAttribute('allowfullscreen','true');frame.onload=function(){fitFacebook();message('');send('manual',{message:'Facebook: use os controlos do vídeo. Seguinte avança a lista manualmente; vídeos privados podem não abrir.'});};document.getElementById('host').appendChild(frame);fitFacebook();
 }else{message('Origem não suportada neste leitor.');send('error',{message:'Abra este vídeo na aplicação de origem.'});}
}
window.addEventListener('message',function(e){
 var d=e.data,controller=e.source===parent;try{controller=controller||(parent.mflCollectionsPip===true&&e.source===(parent.mflCollectionsController||parent.opener)&&e.origin===location.protocol+'//'+location.host);}catch(ignore){}if(!controller||!d||d.source!=='mfl-collections-command')return;
 if(!source){if(d.command!=='load'||typeof d.channel!=='string'||d.channel.length<16)return;source=parent.mflCollectionsPip&&parent.mflCollectionsController?parent.mflCollectionsController:e.source;origin=e.origin;channel=d.channel;load(d.item);return;}
 var pipProxy=false;try{pipProxy=parent.mflCollectionsPip===true&&parent.mflCollectionsController===source&&e.source===parent;}catch(ignore){}
 if((e.source!==source&&!pipProxy)||e.origin!==origin||d.channel!==channel)return;
 if(d.command==='layout'&&facebookFrame){var ratio=Number(d.aspect_ratio);if(isFinite(ratio)&&ratio>=.2&&ratio<=4){facebookAspect=ratio;fitFacebook();}return;}
 try{if(d.command==='play'){if(player.playVideo)player.playVideo();else player.play().catch(function(){send('blocked',{message:'Use os controlos do vídeo para iniciar.'});});}
 else if(d.command==='pause'){if(player.pauseVideo)player.pauseVideo();else player.pause();}
 else if(d.command==='seek'&&isFinite(d.position)&&d.position>=0){if(player.seekTo)player.seekTo(d.position,true);else player.setCurrentTime(d.position);}}
 catch(ignore){send('error',{message:'Este controlo não está disponível neste leitor.'});}
},false);
window.addEventListener('unload',function(){clearInterval(timer);try{if(player)player.destroy();}catch(ignore){}},false);
}());
