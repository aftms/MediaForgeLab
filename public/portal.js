/* ES5, old MAG WebKit. Browsers never obtain a media URL or start streams. */
var MagPortal = (function () {
    var state = { kind:"tv", view:"groups", country:"PT", countryName:"Portugal", origin:"", originName:"", group:"", genre:"", q:"", quality:"auto", favorites:"0", series:"", season:"", seasonName:"" };
    var stack=[], items=[], selected=0, offset=0, total=0, pageSize=10;
    var nativePlayer=null, playerReady=false, initialized=false, playing=false, playingItem=null, paused=false, meta={};
    var playSeq=0, loadSeq=0, detailSeq=0, pageRequest=null, playRequest=null;
    var switchTimer=null, osdTimer=null, detailTimer=null, numberTimer=null, digits="";
    var leaseToken="",leaseTimer=null,leaseRequest=0;
    var updateTimer=null, progressTimer=null, resumePosition=0, completed=false, progressActive=false;
    var artKind="",favoriteTabsFocus=false,menuFocus="list",sidebarIndex=0,sidebarOkTime=0;
    var sidebarButtons=["tab-tv","tab-movie","tab-series","tab-all","personal-button","collections-button","search-button","favorite-button","quality-button","options-button"];
    var favoritePending=false,favoriteLastId="",favoriteLastAttempt=0;
    var searchTimer=null, searchOrigin=null, searchPending=false;
    var seekTimer=null, seekTarget=null, osdTickTimer=null, tracksReady=false, autoAudioDone=false, autoAudioTimer=null, autoAudioAttempts=0, subtitleEnabled=null, pickerSubtitle="";
    var seekDirection=0, seekStarted=0, seekLast=0;
    var fastDirection=0,fastLevel=0,fastTimer=null,fastDuration=0,fastLastPress=0;
    var seekInFlight=null, seekCheckTimer=null, resumeTimer=null, endTimer=null;
    var diagnosticSession=new Date().getTime().toString(36)+"-"+Math.floor(Math.random()*1000000).toString(36),diagnosticSeq=0,bootReported=false;
    var browsePrefs=window.BrowsePrefs.create('catalog-mag',['kind','view','country','countryName','origin','originName','group','genre','q','quality','language','favorites','folder']);
    function browseSlot(){return (state.favorites==="1"?"favorites":state.kind)+":"+state.kind;}
    function restoreBrowse(){state=browsePrefs.read(browseSlot(),state);}
    var overlay="", choices=[], choiceIndex=0, searchDraft="", searchIndex=0, physicalTyping=false, detailPrograms=[];
    var keys="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789".split("").concat(["ESPAÇO","APAGAR","LIMPAR","PESQUISAR","CANCELAR"]);
    var labels={tv:"TV",movie:"Filmes",series:"Séries",all:"Favoritos"};
    var qualities={auto:"Auto · sem repetidos",SD:"SD",HD:"HD",FHD:"Full HD","4K":"4K","8K":"8K",UNKNOWN:"Não indicada",all:"Todas as versões"};
    function el(id){return document.getElementById(id);}
    function text(node,value){while(node.firstChild){node.removeChild(node.firstChild);}node.appendChild(document.createTextNode(String(value)));}
    function status(message){text(el("status"),message);}
    function copy(value){return JSON.parse(JSON.stringify(value));}
    function current(){return items[selected-offset]||null;}
    function optional(method,a,b){try{if(nativePlayer&&nativePlayer[method]){return nativePlayer[method](a,b);}}catch(ignore){}return null;}
    function xhr(path,callback,body){
        var req=new XMLHttpRequest(),done=false,timeout;
        function finish(data){if(done){return;}done=true;window.clearTimeout(timeout);callback(data);}
        req.onreadystatechange=function(){
            if(req.readyState!==4||done){return;}
            var data=null;
            if(req.status===200||path.indexOf("/api/media/")===0){try{data=JSON.parse(req.responseText);}catch(ignore){}}
            finish(data);
        };
        timeout=window.setTimeout(function(){req.onreadystatechange=function(){};try{req.abort();}catch(ignore){}finish(null);},15000);
        try{
            req.open(body?"POST":"GET",path,true);
            if(body){req.setRequestHeader("Content-Type","application/json");req.setRequestHeader("X-MAG-Action",meta.action_token||"");}
            req.send(body?JSON.stringify(body):null);
        }catch(ignore){finish(null);}return req;
    }
    function diagnostic(stage,values,after){
        if(!meta.action_token){if(after){after();}return;}
        var data={session:diagnosticSession,seq:++diagnosticSeq,revision:28,stage:stage,id:playingItem?String(playingItem.id):""},key,done=false,req,timer;
        for(key in values){if(values.hasOwnProperty(key)){data[key]=values[key];}}
        function finish(){if(done){return;}done=true;window.clearTimeout(timer);if(after){after();}}
        timer=window.setTimeout(function(){if(req){req.onreadystatechange=function(){};try{req.abort();}catch(ignore){}}finish();},700);
        req=xhr("/api/player-diagnostics",finish,data);
    }
    function queryString(params){
        var result=[],key;
        for(key in params){if(params.hasOwnProperty(key)&&params[key]!==""){result.push(encodeURIComponent(key)+"="+encodeURIComponent(params[key]));}}
        return result.join("&");
    }
    function resize(){
        var height=window.innerHeight||document.documentElement.clientHeight||576;
        document.body.style.fontSize=Math.max(15,Math.min(38,Math.round(height/29)))+"px";
        var rows=el("list").getElementsByTagName("div"),i;
        for(i=0;i<rows.length;i+=1){rows[i].style.lineHeight=Math.round(height*(favoriteTabsVisible()?0.0423:0.046))+"px";}
    }
    function render(){
        var list=el("list"),i,row,number,name,icon,badge,item=current(),types=["tv","movie","series","all"];
        while(list.firstChild){list.removeChild(list.firstChild);}
        for(i=0;i<types.length;i+=1){el("tab-"+types[i]).className=types[i]===(state.favorites==="1"?"all":state.kind)?"nav-tab active":"nav-tab";}
        el("menu").className=favoriteTabsVisible()?"favorites-view":"";
        el("favorite-tabs").style.display=favoriteTabsVisible()?"block":"none";
        for(i=0;i<3;i+=1){el("favorites-"+types[i]).className="favorite-tab"+(types[i]===state.kind?" active"+(favoriteTabsFocus?" focused":""):"");}
        text(el("footnote"),menuFocus==="sidebar"?"↑ ↓ Escolher opção · OK Abrir · → / BACK Lista":favoriteTabsVisible()?(favoriteTabsFocus?"← → Canais / Filmes / Séries · ↓ / OK Lista · TAB Menu":"← Menu · ↑ No primeiro: tipos · CH+ / CH− Página · OK Abrir"):"← Menu lateral · ↑ ↓ Escolher · CH+ / CH− Página · OK Abrir · BACK Voltar");
        for(i=0;i<sidebarButtons.length;i+=1){var button=el(sidebarButtons[i]);button.className=button.className.replace(/ ?remote-focus/g,"")+(menuFocus==="sidebar"&&sidebarIndex===i?" remote-focus":"");}
        text(el("group"),(state.favorites==="1"?"Favoritos / "+(state.kind==="tv"?"Canais":labels[state.kind]):labels[state.kind])+(state.countryName?" / "+state.countryName:"")+(state.group?" / "+state.group:"")+(state.seasonName?" / "+state.seasonName:"")+(state.originName?" · Origem: "+state.originName:"")+(state.genre?" · Género: "+state.genre:"")+(state.q?" · Pesquisa: "+state.q:""));
        text(el("quality-button"),"Qualidade: "+(state.quality==="auto"?"Auto":qualities[state.quality]));
        text(el("search-button"),state.q?"Pesquisa: "+state.q:"Pesquisar");
        for(i=0;i<items.length;i+=1){
            row=document.createElement("div");row.className="row"+(offset+i===selected&&menuFocus==="list"&&!favoriteTabsFocus?" selected":"");
            number=document.createElement("span");number.className="number";text(number,offset+i+1);
            name=document.createElement("span");name.className="name";
            text(name,(items[i].favorite?"★ ":"")+items[i].name);
            icon=document.createElement("img");icon.className="row-icon";icon.alt="";icon.src="/assets/"+visualKind(items[i])+".png?v=10";
            row.appendChild(number);row.appendChild(icon);row.appendChild(name);
            if(items[i].count!==undefined){badge=document.createElement("span");badge.className="row-count";text(badge,items[i].count+(items[i].kind==="season"?" ep.":"")+"  ›");row.appendChild(badge);row.className+=" directory-row";}
            row.onclick=(function(index){return function(){menuFocus="list";favoriteTabsFocus=false;selected=offset+index;render();openSelected();};}(i));list.appendChild(row);
        }
        text(el("selected-name"),item?item.name:"Sem resultados");
        text(el("selected-group"),item?(item.group||"Escolha com OK"):"Experimente outra pesquisa ou qualidade.");
        text(el("counter"),total?(selected+1)+" de "+total+" · Página "+(Math.floor(offset/pageSize)+1)+"/"+Math.ceil(total/pageSize):"0 resultados");
        text(el("item-quality"),item&&item.quality?"Qualidade: "+(qualities[item.quality]||item.quality):"");
        text(el("favorite-button"),favoriteLabel(item));
        text(el("notice"),!item?"Escolha outra categoria ou pesquisa.":item.kind==="country"||item.kind==="group"?"OK  ·  Explorar esta lista":item.kind==="series"?"OK Temporadas · VERDE Favorito":item.kind==="season"?"OK Episódios · VERDE Série favorita":"OK Reproduzir · VERDE Favorito");
        var visual=visualKind(item);if(artKind!==visual){el("section-art").src="/assets/art-"+visual+".png?v=10";artKind=visual;}
        text(el("art-label"),visual==="country"?"PELO MUNDO":visual==="group"?"EXPLORAR":visual==="movie"?"CINEMA":visual==="series"?"SÉRIES":visual==="episode"?"EPISÓDIO":visual==="all"?"A SUA SELEÇÃO":"EM DIRETO");resize();
    }
    function visualKind(item){var kind=item?item.kind:state.kind;if(kind==="season"){return "series";}return /^(tv|movie|series|all|country|group|episode)$/.test(kind)?kind:"group";}
    function favoriteLabel(item){var kind=item&&(item.kind==="series"||item.kind==="episode"||item.kind==="season")?"série":item&&item.kind==="movie"?"filme":"favorito";return (item&&item.favorite?"Remover ":"Guardar ")+kind;}
    function scheduleDetails(){
        window.clearTimeout(detailTimer);detailSeq+=1;detailPrograms=[];var item=current(),serial=detailSeq;
        text(el("epg-title"),item&&item.kind==="tv"?"Programação · INFO":item&&item.plot?"Sinopse":"");
        text(el("epg"),item&&item.plot?item.plot:item&&item.kind==="tv"?"A consultar programação…":"");
        if(!item||item.kind!=="tv"||overlay==="search"){return;}
        detailTimer=window.setTimeout(function(){
            xhr("/api/epg/"+encodeURIComponent(item.id),function(data){
                if(serial!==detailSeq){return;}var lines=[],i,p;
                if(data&&data.programs){detailPrograms=data.programs;for(i=0;i<data.programs.length&&i<3;i+=1){p=data.programs[i];lines.push(p.start.slice(11,16)+" · "+p.title);}}
                text(el("epg"),lines.length?lines.join("\n"):"Programação não disponibilizada para este canal.");
                if(overlay==="info"){renderInfo();}
            });
        },650);
    }
    function loadPage(position,autoplay){
        if(state.view!=="seasons"&&state.view!=="episodes"){browsePrefs.write(browseSlot(),state);}
        var serial=++loadSeq,params=copy(state);params.offset=Math.max(0,Math.floor(position/pageSize)*pageSize);params.limit=pageSize;
        if(pageRequest){pageRequest.onreadystatechange=function(){};pageRequest.abort();}
        text(el("group"),state.view==="countries"?labels[state.kind]+" · A carregar países…":state.view==="groups"?labels[state.kind]+" · A carregar categorias…":state.view==="seasons"?"A carregar temporadas…":"A carregar esta página…");
        status("A pedir apenas "+pageSize+" entradas…");
        pageRequest=xhr("/api/catalog?"+queryString(params),function(data){
            if(serial!==loadSeq){return;}if(overlay==="search"){searchPending=false;}
            if(!data||!data.items){if(overlay==="search"){items=[];total=0;selected=offset=0;render();}text(el("group"),"Lista indisponível · MENU para repetir");status("Não foi possível carregar. MENU → Atualizar para tentar novamente.");return;}
            total=data.total;offset=data.offset;items=data.items;selected=Math.min(Math.max(0,position),Math.max(0,total-1));
            if(selected<offset||selected>=offset+items.length){selected=offset;}render();scheduleDetails();
            status(nativePlayer?"Leitor MAG pronto · Uma ligação de cada vez":"Modo computador · Sem reprodução de streams");
            if(data.episodes){status(data.episodes.status==="cached_after_error"?"Falha ao verificar episódios. A mostrar a lista guardada.":data.episodes.added+" episódios novos · Lista verificada");}
            if(autoplay&&playing){playSelected();}
        });
    }
    function savePosition(){stack.push({state:copy(state),selected:selected});}
    function cancelPending(){playSeq+=1;window.clearTimeout(autoAudioTimer);autoAudioTimer=null;window.clearTimeout(switchTimer);switchTimer=null;window.clearTimeout(seekTimer);window.clearTimeout(seekCheckTimer);window.clearTimeout(resumeTimer);window.clearTimeout(endTimer);window.clearTimeout(fastTimer);fastDirection=0;seekInFlight=null;seekTarget=null;seekDirection=0;if(playRequest){playRequest.onreadystatechange=function(){};playRequest.abort();playRequest=null;}}
    function releaseLease(){var token=leaseToken;leaseToken="";window.clearTimeout(leaseTimer);xhr("/api/media/stop",function(){},{token:token,owner:diagnosticSession,request_id:leaseRequest});}
    function pulseLease(){var token=leaseToken;if(!playing||!token){return;}xhr("/api/media/pulse",function(data){if(token!==leaseToken){return;}if(!data||data.error){stop();status("A sessão de reprodução terminou. Volte a abrir o conteúdo.");return;}leaseTimer=window.setTimeout(pulseLease,20000);},{token:token});}
    function stop(){
        saveProgress();progressActive=false;window.clearTimeout(progressTimer);
        window.clearTimeout(osdTickTimer);tracksReady=false;closeOverlay();
        cancelPending();window.clearTimeout(osdTimer);window.clearTimeout(numberTimer);digits="";
        playing=false;paused=false;playingItem=null;el("menu").style.display="block";el("osd").style.display="none";render();
        // Stop may synchronously emit event 1. Mark the player stopped first.
        if(nativePlayer){try{nativePlayer.Stop();}catch(ignore){}}
        releaseLease();
    }
    function showOsd(message){
        var item=playingItem||current();text(el("osd-title"),message||(item?(item.favorite?"★ ":"")+item.name:"MediaForgeLab"));
        text(el("osd-hint"),fastDirection?"« / » Velocidade · OK Reproduzir · BACK Cancelar":playing&&item&&item.kind!=="tv"?"← → Ajustar · « » Rápido · VERDE Favorito · MENU Opções":"↑ ↓ / CH+ CH− Mudar · MENU Áudio / Legendas · BACK Parar");
        updateTimeline();window.clearTimeout(osdTickTimer);if(playing){osdTickTimer=window.setTimeout(timelineTick,1000);}
        el("osd").style.display="block";window.clearTimeout(osdTimer);osdTimer=window.setTimeout(function(){if(!seekInFlight&&!fastDirection){el("osd").style.display="none";}},5000);
    }
    function mediaNumber(method){var n=optional(method);return typeof n==="number"&&isFinite(n)&&n>=0?n:null;}
    function timestamp(value){var n=Math.max(0,Math.floor(value)),h=Math.floor(n/3600),m=Math.floor(n/60)%60,s=n%60;return (h?h+":"+(m<10?"0":""):"")+m+":"+(s<10?"0":"")+s;}
    function updateTimeline(){
        var vod=playing&&playingItem&&playingItem.kind!=="tv",duration=fastDirection?fastDuration:seekInFlight?seekInFlight.duration:vod?mediaNumber("GetMediaLen"):null,position=seekTarget!==null?seekTarget:seekInFlight?seekInFlight.target:mediaNumber("GetPosTime");
        el("osd-progress").style.display=vod&&duration>0?"block":"none";
        text(el("osd-time"),vod?(position!==null?timestamp(position):"--:--")+" / "+(duration>0?timestamp(duration):"--:--"):playing?"Em direto":"");
        el("osd-progress-fill").style.width=duration>0&&position!==null?Math.min(100,position/duration*100)+"%":"0%";
    }
    function timelineTick(){if(playing&&el("osd").style.display!=="none"){updateTimeline();osdTickTimer=window.setTimeout(timelineTick,1000);}}
    function setNative(method,value){try{if(!nativePlayer||!nativePlayer[method]){return false;}return nativePlayer[method](value)!==false;}catch(ignore){return false;}}
    function finishSeek(){
        window.clearTimeout(fastTimer);fastDirection=0;
        window.clearTimeout(seekTimer);seekDirection=0;
        if(!playing||seekTarget===null){return;}
        var serial=playSeq;
        // Match the working fixed-jump implementation: leave the key event first.
        seekTimer=window.setTimeout(function(){
            var target=seekTarget;seekTarget=null;
            if(playing&&serial===playSeq&&target!==null){requestSeek(target);}
        },200);
    }
    function requestSeek(target){
        if(!playing||seekInFlight){return;}
        var duration=mediaNumber("GetMediaLen"),from=mediaNumber("GetPosTime"),serial=playSeq;
        if(!duration||from===null||!nativePlayer.SetPosTime){showOsd("Posicionamento indisponível neste conteúdo.");return;}
        target=Math.max(0,Math.min(duration-1,Math.floor(target)));
        // Set state BEFORE entering the native API: it can call onEvent inline.
        seekInFlight={target:target,from:from,duration:duration,serial:serial,started:false,ended:false,time:new Date().getTime()};
        progressActive=false;window.clearTimeout(progressTimer);window.clearTimeout(endTimer);
        showOsd("A posicionar em "+timestamp(target)+" · BACK para voltar");
        diagnostic("seek_call",{target:target,position:Math.floor(from),duration:Math.floor(duration)},function(){
            if(!playing||serial!==playSeq||!seekInFlight){return;}
            if(!setNative("SetPosTime",target)){diagnostic("seek_rejected",{});seekInFlight=null;progressActive=true;progressTimer=window.setTimeout(progressTick,30000);showOsd("Este vídeo ou firmware não permite mudar de posição.");return;}
            diagnostic("seek_return",{target:target});
            if(playing&&serial===playSeq&&seekInFlight){seekCheckTimer=window.setTimeout(checkSeek,800);}
        });
    }
    function checkSeek(){
        var pending=seekInFlight;if(!playing||!pending||pending.serial!==playSeq){return;}
        diagnostic("position_call",{target:pending.target},function(){if(playing&&seekInFlight===pending&&pending.serial===playSeq){readSeekPosition(pending);}});
    }
    function readSeekPosition(pending){
        var position=mediaNumber("GetPosTime"),distance=position===null?Infinity:Math.abs(position-pending.target);
        diagnostic("position_return",{position:position===null?-1:Math.floor(position),target:pending.target});
        if(pending.ended&&position!==null&&position>=pending.duration-3&&pending.target>=pending.duration-3){seekInFlight=null;progressActive=true;completed=true;stop();status("Reprodução terminada.");return;}
        if(position!==null&&(position!==pending.from||pending.target===pending.from)&&(distance<=2||(pending.started&&distance<=10))){
            diagnostic("seek_done",{position:Math.floor(position),target:pending.target});seekInFlight=null;progressActive=true;progressTimer=window.setTimeout(progressTick,30000);showOsd();return;
        }
        if(new Date().getTime()-pending.time>=12000){diagnostic("seek_timeout",{target:pending.target});stop();status("O leitor não retomou após o avanço. Voltámos à lista; pode abrir o filme novamente.");return;}
        seekCheckTimer=window.setTimeout(checkSeek,800);
    }
    function seekBy(delta,gesture){
        if(!playing||!playingItem||playingItem.kind==="tv"){seekDirection=0;showOsd("Avanço e recuo disponíveis nos filmes e episódios.");return;}
        if(seekInFlight){seekDirection=0;showOsd("A aguardar o posicionamento · BACK para voltar");return;}
        var duration=mediaNumber("GetMediaLen"),position=seekTarget!==null?seekTarget:mediaNumber("GetPosTime"),serial=playSeq;
        if(!progressActive||!duration||position===null||!nativePlayer.SetPosTime){seekDirection=0;showOsd("Posicionamento indisponível ou vídeo ainda a iniciar.");return;}
        seekTarget=Math.max(0,Math.min(Math.max(0,duration-1),position+delta));showOsd("Ir para "+timestamp(seekTarget)+(gesture?" · Solte para reproduzir":""));window.clearTimeout(seekTimer);
        seekTimer=window.setTimeout(function(){
            if(serial===playSeq){finishSeek();}
        },gesture?900:200);
    }
    function seekHeld(direction){
        window.clearTimeout(fastTimer);fastDirection=0;
        var now=new Date().getTime();
        if(direction!==seekDirection){seekDirection=direction;seekStarted=now;seekLast=now-100;}
        if(now-seekLast<100){return;}seekLast=now;
        seekBy(direction*(now-seekStarted>=3500?30:now-seekStarted>=1500?10:5),true);
    }
    function fastSeek(direction){
        if(!playing||!playingItem||playingItem.kind==="tv"){showOsd("Avanço rápido disponível nos filmes e episódios.");return;}
        if(seekInFlight){showOsd("A aguardar o posicionamento · BACK para voltar");return;}
        var now=new Date().getTime(),duration=fastDirection?fastDuration:mediaNumber("GetMediaLen"),position=seekTarget!==null?seekTarget:mediaNumber("GetPosTime");
        if(!progressActive||!duration||position===null){showOsd("Posicionamento indisponível ou vídeo ainda a iniciar.");return;}
        if(fastDirection===direction&&now-fastLastPress<350){return;}
        fastLevel=fastDirection===direction?Math.min(2,fastLevel+1):0;fastDirection=direction;fastLastPress=now;fastDuration=duration;
        seekTarget=position;seekDirection=0;window.clearTimeout(seekTimer);window.clearTimeout(fastTimer);closeOverlay();fastTick();
    }
    function fastTick(){
        if(!playing||!fastDirection||seekTarget===null){return;}
        var steps=[10,30,60];seekTarget=Math.max(0,Math.min(fastDuration-1,seekTarget+fastDirection*steps[fastLevel]));
        showOsd((fastDirection>0?"Avançar":"Recuar")+" · Nível "+(fastLevel+1)+"/3 · "+timestamp(seekTarget));
        if(seekTarget>0&&seekTarget<fastDuration-1){fastTimer=window.setTimeout(fastTick,500);}
    }
    function seekKey(code){return code===37||code===66||code===98?-1:code===39||code===70||code===102?1:0;}
    function keyup(event){event=event||window.event;if((event.keyCode||event.which)===13){sidebarOkTime=0;}var direction=seekKey(event.keyCode||event.which);if(direction&&(fastDirection||seekDirection===direction)){if(!fastDirection){finishSeek();}if(event.preventDefault){event.preventDefault();}event.returnValue=false;return false;}return true;}
    function togglePause(){if(!playing){return;}var choosing=seekTarget!==null;finishSeek();if(choosing||seekInFlight){showOsd("A aguardar o posicionamento · BACK para voltar");return;}if(setNative(paused?"Continue":"Pause")){paused=!paused;showOsd(paused?"Em pausa":"A reproduzir");}else{showOsd("Pausa indisponível neste conteúdo.");}}
    function volumeChange(delta){var volume=mediaNumber("GetVolume");if(volume===null||!setNative("SetVolume",Math.max(0,Math.min(100,volume+delta)))){showOsd("Volume indisponível. Use o comando da TV.");return;}showOsd("Volume: "+Math.max(0,Math.min(100,volume+delta))+"%");}
    function toggleMute(){var muted=optional("GetMute");if(muted===null||!setNative("SetMute",muted?0:1)){showOsd("Silêncio indisponível neste firmware.");return;}showOsd(muted?"Som ligado":"Sem som");}
    function playbackNotice(message){picker("Reprodução",[{label:"Voltar ao vídeo",icon:"episode",description:message,action:function(){showOsd();}}],"Disponibilidade no ficheiro");}
    function preferAudio(){
        if(autoAudioDone||autoAudioTimer||!playing||!playingItem||playingItem.kind==="tv"){return;}
        var serial=playSeq;
        // Native callbacks can run inline inside Play/seek. Change tracks only later.
        autoAudioTimer=window.setTimeout(function(){
            autoAudioTimer=null;if(!playing||serial!==playSeq||autoAudioDone){return;}
            if(seekInFlight){preferAudio();return;}
            var tracks=MagTracks.read(optional("GetAudioPIDsEx"));if(!tracks.length){tracks=MagTracks.read(optional("GetAudioPIDs"));}
            autoAudioAttempts+=1;
            if(!tracks.length&&autoAudioAttempts<6){preferAudio();return;}
            autoAudioDone=true;var selected=MagTracks.preferred(tracks);
            if(selected&&Number(optional("GetAudioPID"))!==selected.pid){setNative("SetAudioPID",selected.pid);}
        },250);
    }
    function trackPicker(audio){
        if(!playing){return;}if(!tracksReady){playbackNotice("As faixas ainda estão a carregar. Tente novamente após o vídeo iniciar.");return;}
        var tracks=MagTracks.read(optional(audio?"GetAudioPIDsEx":"GetSubtitlePIDs")),options=[],i,currentPID=optional(audio?"GetAudioPID":"GetSubtitlePID"),serial=playSeq;
        if(audio&&!tracks.length){tracks=MagTracks.read(optional("GetAudioPIDs"));}
        if(!audio){options.push({label:"Desligar legendas",icon:"options",current:subtitleEnabled===false,description:"Oculta as legendas selecionáveis. Texto gravado na imagem não pode ser removido.",action:function(){if(playing&&serial===playSeq&&setNative("SetSubtitles",false)){subtitleEnabled=false;showOsd("Legendas desligadas");}else{showOsd("Não foi possível desligar as legendas.");}}});}
        for(i=0;i<tracks.length;i+=1){options.push((function(track,index){var name=MagTracks.label(track,index,audio);return {label:name,icon:audio?"options":"group",current:currentPID!==null&&Number(currentPID)===track.pid&&(audio||subtitleEnabled===true),description:"Faixa disponibilizada pelo ficheiro. Selecionar não reinicia o vídeo.",action:function(){
            if(!playing||serial!==playSeq){return;}
            var ok=setNative(audio?"SetAudioPID":"SetSubtitlePID",track.pid);if(ok&&audio){autoAudioDone=true;window.clearTimeout(autoAudioTimer);autoAudioTimer=null;}if(ok&&!audio){ok=setNative("SetSubtitles",true);if(ok){subtitleEnabled=true;}}
            showOsd(ok?(audio?"Áudio: ":"Legendas: ")+name:"O leitor não conseguiu selecionar esta faixa.");
        }};}(tracks[i],i)));}
        if(!tracks.length){options.push({label:"Sem faixas disponíveis",icon:"group",description:audio?"O leitor não informou faixas de áudio selecionáveis.":"O leitor não informou legendas selecionáveis neste ficheiro.",action:function(){showOsd(audio?"Sem faixas de áudio selecionáveis.":"Sem legendas selecionáveis neste ficheiro.");}});}
        picker(audio?"Idioma do áudio":"Legendas",options,tracks.length+" faixa(s) disponibilizada(s) pelo leitor");
    }
    function soundMenu(){picker("Som e volume",[
        {label:"Aumentar volume",icon:"quality",badge:"+10",description:"Aumenta o volume da MAG.",action:function(){volumeChange(10);}},
        {label:"Diminuir volume",icon:"quality",badge:"−10",description:"Diminui o volume da MAG.",action:function(){volumeChange(-10);}},
        {label:"Ligar / desligar som",icon:"options",description:"Alterna o silêncio sem mudar a faixa de áudio.",action:toggleMute}
    ],"VOL + / VOL − / MUTE também estão disponíveis");}
    function seekMenu(){picker("Avançar / retroceder",[
        {label:"Avanço rápido",icon:"episode",description:"Percorre a barra continuamente. » aumenta a velocidade; OK aplica e BACK cancela.",action:function(){fastSeek(1);}},
        {label:"Recuo rápido",icon:"episode",description:"Percorre a barra continuamente. « aumenta a velocidade; OK aplica e BACK cancela.",action:function(){fastSeek(-1);}},
        {label:"Recuar 5 segundos",icon:"episode",action:function(){seekBy(-5);}},
        {label:"Avançar 5 segundos",icon:"episode",action:function(){seekBy(5);}},
        {label:"Recuar 30 segundos",icon:"episode",action:function(){seekBy(-30);}},
        {label:"Avançar 30 segundos",icon:"episode",action:function(){seekBy(30);}}
    ],"« / »: rápido · ← / →: ajuste fino · OK: aplicar");}
    function playbackMenu(){picker("Opções de reprodução",[
        {label:paused?"Retomar":"Pausar",icon:"episode",description:"Pausa ou retoma o vídeo atual.",action:togglePause},
        {label:"Avançar / retroceder",icon:"episode",badge:"« »",description:"« / » percorre a barra em 3 velocidades; OK aplica. Setas: ajuste de 5 segundos.",action:seekMenu},
        {label:"Idioma do áudio",icon:"options",description:"Escolha entre as faixas de áudio existentes neste conteúdo.",action:function(){trackPicker(true);}},
        {label:"Legendas",icon:"group",description:"Selecione uma faixa de legendas existente ou desligue as legendas.",action:function(){trackPicker(false);}},
        {label:"Som e volume",icon:"quality",description:"Controle o volume da MAG e o silêncio.",action:soundMenu},
        {label:"Qualidade do vídeo",icon:"quality",description:"Este conteúdo usa a qualidade do ficheiro. O filtro da TV não converte vídeo.",action:function(){playbackNotice("Qualidade do ficheiro original. Para outra versão, escolha outro título no catálogo.");}},
        {label:"Informações",icon:"tv",description:"Descrição do título ou programação do canal.",action:showInfo},
        {label:favoriteLabel(playingItem),icon:"all",description:"Guarde ou remova este favorito sem parar o vídeo. Num episódio, guarda a série inteira.",action:favorite}
    ],"Áudio, legendas e controlos do vídeo atual");}
    function playSelected(){
        var item=current();if(!item){return;}if(!nativePlayer){status("Pré-visualização no computador. A reprodução só é ativada na MAG.");return;}
        saveProgress();progressActive=false;window.clearTimeout(progressTimer);resumePosition=0;completed=false;
        tracksReady=false;subtitleEnabled=null;autoAudioDone=false;autoAudioAttempts=0;
        cancelPending();var serial=playSeq;
        window.clearTimeout(leaseTimer);leaseToken="";
        playing=false;
        try{if(!playerReady){nativePlayer.InitPlayer();playerReady=true;optional("SetTopWin",0);optional("EnableSpatialNavigation",false);optional("EnableVKButton",false);}nativePlayer.Stop();}catch(ignore){stop();status("Não foi possível iniciar ou parar o leitor.");return;}
        playing=true;paused=false;playingItem=item;el("menu").style.display="none";showOsd("A abrir · "+item.name);
        switchTimer=window.setTimeout(function(){
            switchTimer=null;if(!playing||serial!==playSeq){return;}
            leaseRequest=serial;
            playRequest=xhr("/api/media/mag",function(data){
                if(!playing||serial!==playSeq){return;}playRequest=null;
                if(!data||!data.url){stop();status(data&&data.error?data.error:"Não foi possível obter este conteúdo.");return;}
                leaseToken=data.token;window.clearTimeout(leaseTimer);leaseTimer=window.setTimeout(pulseLease,20000);
                resumePosition=data.progress&&!data.progress.completed?Number(data.progress.position)||0:0;
                try{nativePlayer.Play((meta.player_solution||"ffmpeg")+" "+data.url);showOsd();}
                catch(ignore){stop();status("O leitor recusou este formato.");}
            },{id:item.id,owner:diagnosticSession,request_id:serial});
        },meta.switch_delay_ms||1000);
    }
    function openSelected(){
        menuFocus="list";favoriteTabsFocus=false;
        if(overlay==="search"){
            if(searchPending){return;}var origin=searchOrigin;closeOverlay();if(origin){stack.push(origin);}
        }
        var item=current();if(!item){return;}
        if(item.kind==="country"){savePosition();state.country=item.id.slice(8);state.countryName=item.name;state.view="groups";state.group="";loadPage(0,false);}
        else if(item.kind==="group"){savePosition();state.group=item.group;state.view="items";loadPage(0,false);}
        else if(item.kind==="series"){savePosition();state.view="seasons";state.series=item.id;state.group=item.name;state.q="";state.season="";state.seasonName="";loadPage(0,false);}
        else if(item.kind==="season"){savePosition();state.view="episodes";state.season=item.season;state.seasonName=item.name;loadPage(0,false);}
        else{playSelected();}
    }
    function move(delta){
        if(!playing){menuFocus="list";favoriteTabsFocus=false;}
        if(!total){return;}var target=((selected+delta)%total+total)%total;
        if(playing){saveProgress();progressActive=false;cancelPending();playing=false;optional("Stop");playing=true;}
        if(target>=offset&&target<offset+items.length){selected=target;render();scheduleDetails();if(playing){playSelected();}}
        else{loadPage(target,playing);}
    }
    function closeOverlay(){
        if(overlay==="search"){window.clearTimeout(searchTimer);loadSeq+=1;if(pageRequest){pageRequest.onreadystatechange=function(){};pageRequest.abort();}searchOrigin=null;searchPending=false;}
        overlay="";el("search-panel").style.display="none";el("picker").style.display="none";el("help").style.display="none";el("info-panel").style.display="none";el("source-panel").style.display="none";el("source-input").value="";
    }
    function menuPaneKey(code){
        if(code===9){menuFocus=menuFocus==="sidebar"?"list":"sidebar";favoriteTabsFocus=false;render();return true;}
        if(menuFocus==="sidebar"){
            if(code===38||code===40){sidebarIndex=(sidebarIndex+(code===38?-1:1)+sidebarButtons.length)%sidebarButtons.length;render();return true;}
            if(code===39||code===8||code===27){menuFocus="list";render();return true;}
            if(code===13){sidebarOkTime=new Date().getTime();el(sidebarButtons[sidebarIndex]).onclick();return true;}
            return code===37;
        }
        if(favoriteTabsFocus){return false;}
        if(code===37){menuFocus="sidebar";render();return true;}
        return code===39;
    }
    function favoriteTabsVisible(){return state.favorites==="1"&&state.view==="items";}
    function selectFavoriteKind(kind,focus){
        if(playing){stop();}closeOverlay();stack=[];menuFocus="list";sidebarIndex=3;favoriteTabsFocus=!!focus;
        state.kind=kind;state.origin="";state.originName="";state.favorites="1";state.view="items";state.country="";state.countryName="";state.group="";state.genre="";state.q="";state.series="";state.season="";state.seasonName="";restoreBrowse();loadPage(0,false);
    }
    function favoriteKindPicker(){picker("Favoritos",[
        {label:"Canais",icon:"tv",description:"Os seus canais favoritos.",action:function(){selectFavoriteKind("tv",false);}},
        {label:"Filmes",icon:"movie",description:"Os seus filmes favoritos.",action:function(){selectFavoriteKind("movie",false);}},
        {label:"Séries",icon:"series",description:"As suas séries favoritas. OK abre as temporadas.",action:function(){selectFavoriteKind("series",false);}}
    ]);}
    function favoriteTabKey(code){
        if(!favoriteTabsFocus){if(code===38&&selected===0){favoriteTabsFocus=true;render();return true;}return false;}
        if(code===37||code===39){var kinds=["tv","movie","series"],i;for(i=0;i<3;i+=1){if(kinds[i]===state.kind){selectFavoriteKind(kinds[(i+(code===37?2:1))%3],true);break;}}return true;}
        if(code===13||code===40){favoriteTabsFocus=false;render();return true;}
        return code===38;
    }
    function selectKind(kind,allCountries){
        if(kind==="all"){selectFavoriteKind("tv",false);return;}menuFocus="list";sidebarIndex=kind==="movie"?1:kind==="series"?2:0;favoriteTabsFocus=false;
        if(playing){stop();}closeOverlay();stack=[];state.kind=kind;state.view=kind==="tv"&&allCountries?"countries":"groups";
        state.origin="";state.originName="";state.country=kind==="tv"&&!allCountries?"PT":"";state.countryName=state.country==="PT"?"Portugal":"";state.group="";state.genre="";state.q="";state.series="";state.season="";state.seasonName="";state.favorites="0";if(!allCountries){restoreBrowse();}loadPage(0,false);
    }
    function nextKind(){var kinds=["tv","movie","series","all"],i;for(i=0;i<kinds.length;i+=1){if((state.favorites==="1"?"all":state.kind)===kinds[i]){selectKind(kinds[(i+1)%kinds.length]);return;}}}
    function back(){
        if(playing){diagnostic("back",{});}
        if(fastDirection){window.clearTimeout(fastTimer);fastDirection=0;seekTarget=null;seekDirection=0;showOsd("Escolha cancelada · A reprodução continua");return;}
        if(overlay){closeOverlay();return;}if(playing){stop();return;}if(state.q){state.q="";loadPage(0,false);return;}
        if(stack.length){var previous=stack.pop();state=previous.state;loadPage(previous.selected,false);}
        else if(state.kind==="tv"&&state.view!=="countries"){selectKind("tv",true);}else if(state.kind!=="tv"){selectKind("tv");}
    }
    function favorite(){
        var item=playing?playingItem:current();
        if(!item||item.kind==="country"||item.kind==="group"){status("Escolha um canal, filme ou série para guardar.");return;}
        if(item.kind==="season"){item=copy(item);item.id=state.series;item.kind="series";}
        var now=new Date().getTime(),repeat=favoriteLastId===item.id&&now-favoriteLastAttempt<700,series=state.series;
        favoriteLastId=item.id;favoriteLastAttempt=now;
        if(favoritePending||repeat){return;}
        favoritePending=true;
        xhr("/api/favorite",function(data){
            favoritePending=false;
            if(!data){if(playing){showOsd("Não foi possível guardar o favorito. Tente novamente.");}else{status("Não foi possível guardar o favorito. Tente novamente.");}return;}
            item.favorite=data.favorite;if((item.kind==="episode"||item.kind==="series")&&state.series===series){for(var i=0;i<items.length;i+=1){if(items[i].kind==="episode"||items[i].kind==="season"){items[i].favorite=data.favorite;}}}render();
            if(playing){showOsd(data.favorite?"★ Guardado nos favoritos":"Removido dos favoritos");}
            else if(state.favorites==="1"){loadPage(selected,false);}else{status(data.favorite?"★ Favorito guardado":"Favorito removido");}
        },{id:item.id,favorite:!item.favorite});
    }
    function renderPicker(){
        var node=el("picker-list"),i,button,icon,label,badge,start=Math.floor(choiceIndex/8)*8;while(node.firstChild){node.removeChild(node.firstChild);}
        for(i=start;i<choices.length&&i<start+8;i+=1){
            button=document.createElement("div");button.className="picker-row"+(i===choiceIndex?" selected":"");
            icon=document.createElement("img");icon.className="picker-icon";icon.alt="";icon.src="/assets/"+(choices[i].icon||"options")+".png?v=10";button.appendChild(icon);
            label=document.createElement("span");label.className="picker-label";text(label,choices[i].label);button.appendChild(label);
            badge=document.createElement("span");badge.className="picker-badge";text(badge,choices[i].current?"Em uso":choices[i].badge||"›");button.appendChild(badge);
            button.onclick=(function(index){return function(){choiceIndex=index;choosePicker();};}(i));node.appendChild(button);
        }
        text(el("picker-description"),choices[choiceIndex].description||"Escolha com OK.");
        text(el("picker-subtitle"),pickerSubtitle+(choices.length>8?" · "+(choiceIndex+1)+" / "+choices.length:""));
    }
    function picker(title,options,subtitle){closeOverlay();overlay="picker";choices=options;choiceIndex=0;pickerSubtitle=subtitle||"Biblioteca e reprodução";for(var i=0;i<choices.length;i+=1){if(choices[i].current){choiceIndex=i;break;}}text(el("picker-title"),title);renderPicker();el("picker").style.display="block";}
    function choosePicker(){var action=choices[choiceIndex].action;closeOverlay();action();}
    function qualityPicker(){
        var options=[],key,descriptions={auto:"Preferência: Full HD, HD, 4K, SD, não indicada, 8K. Não adapta à velocidade da ligação.",SD:"Mostra as versões identificadas como SD pelo fornecedor.",HD:"Mostra as versões identificadas como HD pelo fornecedor.",FHD:"Mostra as versões identificadas como Full HD pelo fornecedor.","4K":"A MAG324 não suporta vídeo 4K. O filtro apenas mostra estes títulos.","8K":"A MAG324 não suporta vídeo 8K. O filtro apenas mostra estes títulos.",UNKNOWN:"Canais cujo nome não indica uma qualidade reconhecida.",all:"Mostra todas as versões, incluindo canais repetidos em qualidades diferentes."};
        for(key in qualities){if(qualities.hasOwnProperty(key)){options.push((function(k){return {label:qualities[k],icon:"quality",current:k===state.quality,description:descriptions[k],action:function(){state.quality=k;try{window.localStorage.setItem("mag-quality-v2",k);}catch(ignore){}loadPage(0,false);}};}(key)));}}
        if(playing){stop();}picker("Qualidade da TV",options,"Escolha a versão dos canais");
    }
    function vodFilterPicker(view){
        if(state.kind!=="movie"&&state.kind!=="series"){status("Escolha Filmes ou Séries para usar este filtro.");return;}
        var kind=state.kind,stamp=loadSeq;
        xhr("/api/catalog?"+queryString({view:view,kind:kind,country:state.country,client:"web",limit:240}),function(data){
            if(state.kind!==kind||stamp!==loadSeq){return;}
            if(!data||!data.items){status("Não foi possível carregar os filtros. Tente novamente.");return;}
            var countries=view==="countries",rows=[{id:countries?"country:":"genre:",name:countries?"Todos os países / idiomas":"Todos os géneros"}].concat(data.items),options=[],i;
            for(i=0;i<rows.length;i+=1){options.push((function(row){var value=row.id.slice(countries?8:6);return {label:row.name,icon:countries?"country":"group",current:value===(countries?state.country:state.genre),description:countries?"País / idioma da versão no catálogo; não indica o país de produção.":"Género indicado nos metadados ou categorias do catálogo.",action:function(){
                if(countries){state.country=value;state.countryName=value?row.name:"";state.group="";state.genre="";}else{state.genre=value;if(state.view==="seasons"||state.view==="episodes"){state.group="";}}
                state.view="items";state.series="";state.season="";state.seasonName="";stack=[];loadPage(0,false);
            }};}(rows[i])));}
            picker(countries?"País / idioma":"Género",options);
        });
    }
    function originPicker(){
        var stamp=loadSeq;
        status("A consultar origens…");
        xhr("/api/catalog?"+queryString({view:"origins",kind:"tv",country:state.country,limit:30}),function(data){
            if(stamp!==loadSeq||state.kind!=="tv"){return;}
            if(!data){status("Não foi possível consultar as origens.");return;}
            var sources=[{id:"origin:",name:"Todas as origens"}].concat(data.items);
            function draw(focus){var options=[],selected=state.origin?state.origin.split(","):[],i;
                for(i=0;i<sources.length;i+=1){options.push((function(row,index){var code=row.id.slice(7),checked=code?selected.indexOf(code)!==-1:!selected.length;return {label:(checked?"✓ ":"□ ")+row.name,icon:"tv",badge:checked?"Selecionada":"",description:"OK marca ou desmarca. Pode escolher várias origens. BACK regressa aos canais.",action:function(){var found=selected.indexOf(code);if(!code){selected=[];}else if(found<0){selected.push(code);}else{selected.splice(found,1);}state.origin=selected.sort().join(",");var names=[];for(var n=1;n<sources.length;n+=1){if(selected.indexOf(sources[n].id.slice(7))!==-1){names.push(sources[n].name);}}state.originName=names.join(" + ");stack=[];loadPage(0,false);draw(index);}};}(sources[i],i)));}
                options.push({label:"Concluir",icon:"tv",action:function(){}});picker("Origem dos canais",options,"OK marcar / desmarcar · BACK concluir");choiceIndex=focus||0;renderPicker();
            }
            status("");draw(0);
        });
    }
    function help(){closeOverlay();overlay="help";el("help").style.display="block";}
    function renderInfo(){
        var item=playing?playingItem:current(),lines=[],i,p;text(el("info-title"),item?item.name:"Informação");
        if(item){lines.push(item.group||"");if(item.plot){lines.push(item.plot);}}
        for(i=0;i<detailPrograms.length;i+=1){p=detailPrograms[i];lines.push(p.start.slice(11,16)+"–"+p.end.slice(11,16)+" · "+p.title+"\n"+(p.description||""));}
        if(item&&item.kind==="tv"&&!detailPrograms.length){lines.push("Programação não disponibilizada para este canal.");}text(el("info-text"),lines.join("\n\n"));
    }
    function showInfo(){finishSeek();closeOverlay();overlay="info";renderInfo();el("info-panel").style.display="block";}
    function optionsMenu(){if(playing){finishSeek();playbackMenu();return;}var menu=[
        {label:"Pesquisar",icon:"search",description:"Abra o teclado no ecrã. Use as setas e OK; escolha Ver lista para ver os resultados.",action:search},
        {label:favoriteLabel(current()),icon:"all",description:"Guarde ou remova o canal, filme ou série selecionado. Primeiro escolha um título na lista.",action:favorite},
        {label:"Abrir favoritos",icon:"all",description:"Veja os canais, filmes e séries que guardou.",action:function(){selectKind("all");}},
        {label:"Qualidade da TV",icon:"quality",badge:state.quality==="auto"?"Auto":state.quality,description:"Escolha a qualidade e controle as versões repetidas dos canais.",action:qualityPicker},
        {label:state.favorites==="1"?"Tipo de favorito":"Países e categorias",icon:state.favorites==="1"?"all":"country",description:state.favorites==="1"?"Escolha Canais, Filmes ou Séries nos seus favoritos.":"Volte ao início da secção para explorar os conteúdos por país ou categoria.",action:function(){if(state.favorites==="1"){favoriteKindPicker();}else{selectKind(state.kind,true);}}},
        {label:"Recarregar esta lista",icon:"group",description:"Volta a carregar a página atual a partir do catálogo já guardado.",action:function(){loadPage(selected,false);loadLibrary();}},
        {label:"Guia do comando",icon:"options",description:"Consulte as teclas para pesquisar, guardar favoritos e controlar a reprodução.",action:help},
        {label:"Programação e detalhes",icon:"tv",badge:"INFO",description:"Veja o EPG do canal selecionado ou a descrição do filme ou episódio.",action:showInfo},
        {label:"Atualizar catálogo",icon:"refresh",description:"Consulte novidades de canais, filmes e séries no serviço, em segundo plano.",action:checkUpdates},
        {label:"Origem do catálogo",icon:"group",description:"Altere o URL do serviço. Os dados de acesso permanecem ocultos.",action:sourceSettings}
        ].concat(state.kind==="movie"||state.kind==="series"?[
        {label:"Filtrar por país / idioma",icon:"country",description:"Escolha a versão do catálogo por país ou idioma.",action:function(){vodFilterPicker("countries");}},
        {label:"Filtrar por género",icon:"group",description:"Ação, comédia, drama e outros géneros disponíveis.",action:function(){vodFilterPicker("genres");}}
    ]:[]);if(state.kind==="tv"){menu.splice(5,0,{label:"Origem dos canais",icon:"tv",badge:state.originName||"Todas",description:"Escolha VO/Vodafone, MEO ou outra origem indicada pelo fornecedor.",action:originPicker});}picker("Opções",menu);}
    function updateStatus(data){
        window.clearTimeout(updateTimer);
        if(!data){text(el("update-status"),"Não foi possível consultar a atualização. Tente novamente.");return;}
        var message=data.running?data.stage||"A verificar…":data.error||"",a=data.summary&&data.summary.added;
        if(!message&&a){message=a.tv+" canais, "+a.movie+" filmes e "+a.series+" séries adicionados";}
        text(el("update-button"),data.running?"Verificação em curso…":"Verificar atualizações");
        text(el("update-status"),(message?message+" · ":"")+"Última atualização: "+(data.last_success?data.last_success.replace("T"," ").replace("Z"," UTC"):"ainda não realizada"));
        if(data.running){updateTimer=window.setTimeout(pollUpdates,3000);}
    }
    function pollUpdates(){xhr("/api/refresh",updateStatus);}
    function checkUpdates(){
        // Never Stop/Play or refresh the selected page as part of a catalog update.
        text(el("update-status"),"A iniciar verificação…");
        xhr("/api/refresh",updateStatus,{});
    }
    function sourceSettings(){
        closeOverlay();overlay="source";el("source-panel").style.display="block";
        text(el("source-server"),"A consultar configuração…");
        xhr("/api/source",function(data){text(el("source-server"),data&&data.configured?"Servidor configurado: "+data.server:"Origem indisponível");});
        el("source-input").focus();
    }
    function saveSource(){
        var value=el("source-input").value;
        xhr("/api/source",function(data){
            el("source-input").value="";
            if(!data){text(el("source-server"),"Não foi possível guardar. Verifique o URL ou aguarde o fim da atualização.");return;}
            closeOverlay();status("Origem guardada. Escolha Verificar atualizações para aplicar.");
        },{url:value});
    }
    function saveProgress(){
        if(!playing||!progressActive||!playingItem||playingItem.kind==="tv"){return;}
        var position=optional("GetPosTime"),duration=optional("GetMediaLen");
        if(typeof position!=="number"||position<0||!isFinite(position)){return;}
        xhr("/api/progress",function(){},{id:playingItem.id,position:Math.floor(position),duration:typeof duration==="number"&&isFinite(duration)&&duration>0?Math.floor(duration):0,completed:completed});
    }
    function progressTick(){saveProgress();if(playing){progressTimer=window.setTimeout(progressTick,30000);}}
    function renderSearch(){
        text(el("search-query"),searchDraft||"Escreva o nome do canal, filme ou série…");
        var node=el("search-keys"),i,key;while(node.firstChild){node.removeChild(node.firstChild);}
        for(i=0;i<keys.length;i+=1){key=document.createElement("span");key.className="search-key"+(i>=36?" search-action":"")+(i===searchIndex?" selected":"");text(key,keys[i]==="PESQUISAR"?"Ver lista":keys[i]);key.onclick=(function(index){return function(){searchIndex=index;searchKey();};}(i));node.appendChild(key);}
    }
    function search(){
        favoriteTabsFocus=false;if(playing){stop();}closeOverlay();overlay="search";searchOrigin={state:copy(state),selected:selected};searchDraft=state.q;searchIndex=0;physicalTyping=false;window.clearTimeout(detailTimer);detailSeq+=1;renderSearch();el("search-panel").style.display="block";}
    function searchState(origin){
        var next=copy(origin.state),query=searchDraft.replace(/^\s+|\s+$/g,"");next.q=query;
        if(query){next.view="items";next.group="";next.series="";next.season="";next.seasonName="";}return next;
    }
    function liveSearch(){
        window.clearTimeout(searchTimer);loadSeq+=1;searchPending=true;
        if(pageRequest){pageRequest.onreadystatechange=function(){};pageRequest.abort();}
        window.clearTimeout(detailTimer);detailSeq+=1;status("A filtrar resultados…");
        searchTimer=window.setTimeout(function(){if(overlay!=="search"||!searchOrigin){return;}state=searchState(searchOrigin);loadPage(0,false);},250);
    }
    function applySearch(){menuFocus="list";favoriteTabsFocus=false;var origin=searchOrigin,next=origin?searchState(origin):copy(state);closeOverlay();if(origin){stack.push(origin);}state=next;loadPage(0,false);}
    function cancelSearch(){var origin=searchOrigin;closeOverlay();if(origin){state=origin.state;loadPage(origin.selected,false);}}
    function moveSearch(code){
        if(code===37||code===39){searchIndex=(searchIndex+(code===37?-1:1)+keys.length)%keys.length;}
        else{var row=searchIndex<36?Math.floor(searchIndex/6):6+Math.floor((searchIndex-36)/3),column=searchIndex<36?searchIndex%6:(searchIndex-36)%3;
            row=Math.max(0,Math.min(7,row+(code===38?-1:1)));searchIndex=(row<6?row*6:36+(row-6)*3)+Math.min(column,row<6?5:row===6?2:1);}
        renderSearch();
    }
    function searchKey(){
        var key=keys[searchIndex];if(key==="PESQUISAR"){applySearch();return;}if(key==="CANCELAR"){cancelSearch();return;}
        if(key==="APAGAR"){searchDraft=searchDraft.slice(0,-1);}else if(key==="LIMPAR"){searchDraft="";}else{searchDraft=(searchDraft+(key==="ESPAÇO"?" ":key)).slice(0,80);}renderSearch();liveSearch();
    }
    function keypress(event){
        event=event||window.event;var code=event.charCode||event.which||event.keyCode;
        if(typeof event.charCode==="number"&&event.charCode===0){return true;}
        if(overlay==="search"&&code>=32&&!event.ctrlKey&&!event.altKey){searchDraft=(searchDraft+String.fromCharCode(code)).slice(0,80);physicalTyping=true;renderSearch();liveSearch();if(event.preventDefault){event.preventDefault();}event.returnValue=false;return false;}return true;
    }
    function chooseNumber(){menuFocus="list";favoriteTabsFocus=false;var position=parseInt(digits,10)-1;digits="";window.clearTimeout(numberTimer);el("osd").style.display="none";if(position>=0&&position<total){loadPage(position,playing);}else{status("Número inexistente nesta lista.");}}
    function keydown(event){
        event=event||window.event;var code=event.keyCode||event.which,handled=true,volume;
        // Holding OK on a sidebar action must not activate the next screen as well.
        if(code!==13){sidebarOkTime=0;}else if(sidebarOkTime&&new Date().getTime()-sidebarOkTime<700){sidebarOkTime=new Date().getTime();if(event.preventDefault){event.preventDefault();}event.returnValue=false;return false;}
        // MAG remote media buttons differ from the colour buttons by ALT.
        if(playing&&event.altKey&&(code===66||code===98||code===70||code===102||code===82||code===114||code===83||code===115||code===96||code===192||code===121||code===89)){
            if(code===66||code===98){fastSeek(-1);}else if(code===70||code===102){fastSeek(1);}
            else if(code===82||code===114){togglePause();}else if(code===83||code===115){stop();}
            else if(code===96||code===192){toggleMute();}else{showInfo();}
        }else if(overlay==="source"){
            if(code===27){closeOverlay();}else if(code===13){saveSource();}else{handled=false;}
        }else if(overlay==="search"){
            if(code===27){cancelSearch();}else if(code===8){searchDraft=searchDraft.slice(0,-1);renderSearch();liveSearch();}
            else if(code===115){applySearch();}else if(code===13){if(physicalTyping){applySearch();}else{searchKey();}}
            else if(code>=37&&code<=40){physicalTyping=false;moveSearch(code);}
            else{handled=false;}
        }else if(overlay==="picker"){
            if(code===8||code===27){closeOverlay();}else if(code===13){choosePicker();}else if(code===38||code===40){choiceIndex=(choiceIndex+(code===38?-1:1)+choices.length)%choices.length;renderPicker();}
        }else if(overlay){if(code===13||code===8||code===27||code===73||code===89){closeOverlay();}else if(overlay==="info"&&(code===38||code===40)){el("info-text").scrollTop+=(code===38?-80:80);}}
        else if(code>=48&&code<=57&&!event.altKey&&!event.ctrlKey){if(playing&&playingItem&&playingItem.kind!=="tv"){showOsd("Use ← → para avançar ou retroceder.");}else{digits=(digits+String(code-48)).slice(-6);window.clearTimeout(numberTimer);showOsd("Posição "+digits);numberTimer=window.setTimeout(chooseNumber,1800);}}
        else if(!playing&&menuPaneKey(code)){}
        else if(!playing&&favoriteTabsVisible()&&favoriteTabKey(code)){}
        else{
            switch(code){
            case 38:move(playing?1:-1);break;case 40:move(playing?-1:1);break;
            case 37:if(playing){seekHeld(-1);}break;case 39:if(playing){seekHeld(1);}break;
            case 33:move(playing?1:-pageSize);break;case 34:move(playing?-1:pageSize);break;case 9:move(event.shiftKey?-1:1);break;
            case 13:if(digits){chooseNumber();}else if(playing&&seekTarget!==null){finishSeek();}else if(playing){showOsd();}else{openSelected();}break;
            case 8:case 27:back();break;case 83:stop();break;
            case 112:nextKind();break;case 113:favorite();break;case 114:search();break;case 115:selectKind("all");break;
            case 122:optionsMenu();break;case 73:case 89:showInfo();break;
            case 19:case 32:case 80:togglePause();break;
            case 107:case 109:volumeChange(code===107?5:-5);break;
            case 192:toggleMute();break;
            default:handled=false;
            }
        }
        if(handled){if(event.preventDefault){event.preventDefault();}event.returnValue=false;return false;}return true;
    }
    function loadLibrary(){
        xhr("/api/library",function(data){
            if(!data||!data.counts){text(el("library-counts"),"Contagem indisponível · MENU para repetir");return;}meta=data;
            if(!bootReported){bootReported=true;diagnostic("boot",{native:!!nativePlayer});}
            text(el("library-counts"),(data.counts.tv||0)+" TV · "+(data.counts.movie||0)+" filmes · "+(data.counts.series||0)+" séries");
        });
    }
    function init(){
        if(initialized){return;}initialized=true;
        status("A iniciar menus…");
        try{
            if(window.gSTB&&window.gSTB.Play&&window.gSTB.Stop){nativePlayer=window.gSTB;}else if(window.stb&&window.stb.Play&&window.stb.Stop){nativePlayer=window.stb;}
        }catch(ignore){nativePlayer=null;}
        try{var saved=window.localStorage.getItem("mag-quality-v2");if(qualities[saved]){state.quality=saved;}}catch(ignore){}
        var last=browsePrefs.last("tv:tv").split(":");if(["tv","movie","series","favorites"].indexOf(last[0])!==-1&&["tv","movie","series"].indexOf(last[1])!==-1){state.kind=last[1];state.favorites=last[0]==="favorites"?"1":"0";state.country=last[0]==="tv"?"PT":"";state.countryName=state.country?"Portugal":"";}restoreBrowse();sidebarIndex=state.favorites==="1"?3:state.kind==="movie"?1:state.kind==="series"?2:0;
        document.onkeydown=keydown;document.onkeyup=keyup;document.onkeypress=keypress;window.onresize=resize;
        window.onunload=function(){saveProgress();releaseLease();if(nativePlayer){try{nativePlayer.Stop();}catch(ignore){}}};
        el("favorites-tv").onclick=function(){selectFavoriteKind("tv",false);};el("favorites-movie").onclick=function(){selectFavoriteKind("movie",false);};el("favorites-series").onclick=function(){selectFavoriteKind("series",false);};
        el("tab-tv").onclick=function(){selectKind("tv");};el("tab-movie").onclick=function(){selectKind("movie");};el("tab-series").onclick=function(){selectKind("series");};el("tab-all").onclick=function(){selectKind("all");};
        el("search-button").onclick=search;el("quality-button").onclick=qualityPicker;el("favorite-button").onclick=favorite;el("options-button").onclick=optionsMenu;
        el("collections-button").onclick=function(){window.location.href="/tv/collections.html?client=mag";};
        el("personal-button").onclick=function(){window.location.href="/tv/personal.html?client=mag";};
        el("update-button").onclick=checkUpdates;el("source-save").onclick=saveSource;
        loadPage(0,false);loadLibrary();pollUpdates();
    }
    function nativeEvent(code){
        var serial=playSeq;
        if(playing&&/^(1|2|4|5|7)$/.test(String(code))){diagnostic("native_event",{event:Number(code)});}
        if(playing&&!switchTimer&&Number(code)===2){tracksReady=true;preferAudio();}
        else if(playing&&!switchTimer&&Number(code)===5){window.clearTimeout(endTimer);endTimer=window.setTimeout(function(){if(playing&&serial===playSeq){stop();status("Sem reprodução. Verifique ligação única, formato e disponibilidade.");}},0);}
        // Event 1 also means stream discontinuity, not just end of film.
        // Never Stop or seek from inside a native event callback.
        else if(playing&&!switchTimer&&playingItem&&playingItem.kind!=="tv"&&Number(code)===1){
            if(seekInFlight){seekInFlight.ended=true;return;}
            window.clearTimeout(endTimer);endTimer=window.setTimeout(function(){if(!playing||serial!==playSeq||seekInFlight){return;}var pos=mediaNumber("GetPosTime"),len=mediaNumber("GetMediaLen");completed=len>0&&pos!==null&&pos>=len-3;stop();status(completed?"Reprodução terminada.":"A transmissão foi interrompida. Pode voltar a abrir o título.");},300);
        }
        else if(playing&&!switchTimer&&Number(code)===4){
            tracksReady=true;preferAudio();window.clearTimeout(endTimer);
            if(seekInFlight){seekInFlight.started=true;return;}
            progressActive=true;window.clearTimeout(progressTimer);progressTimer=window.setTimeout(progressTick,30000);
            if(resumePosition>0){var target=resumePosition;resumePosition=0;window.clearTimeout(resumeTimer);resumeTimer=window.setTimeout(function(){if(playing&&serial===playSeq&&!seekInFlight){requestSeek(target);}},200);}
        }
    }
    return {init:init,keydown:keydown,keyup:keyup,keypress:keypress,stop:stop,nativeEvent:nativeEvent};
}());
var stbEvent={onEvent:function(code){MagPortal.nativeEvent(code);},event:0};
