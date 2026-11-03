/* ES5. Parse legacy MAG track descriptors as data, never executable code. */
var MagTracks = (function () {
    function decodeQuoted(token) {
        if(token.charAt(0)==='"'){return JSON.parse(token);}
        var value="",i,c,esc,hex,map={b:"\b",f:"\f",n:"\n",r:"\r",t:"\t"};
        for(i=1;i<token.length-1;i+=1){
            c=token.charAt(i);
            if(c!=="\\"){value+=c;continue;}
            i+=1;esc=token.charAt(i);
            if(esc==="u"){hex=token.substr(i+1,4);if(!/^[0-9a-f]{4}$/i.test(hex)){throw new Error("Invalid escape");}value+=String.fromCharCode(parseInt(hex,16));i+=4;}
            else if(esc==="'"||esc==='"'||esc==="\\"||esc==="/"){value+=esc;}
            else if(map.hasOwnProperty(esc)){value+=map[esc];}else{throw new Error("Invalid escape");}
        }
        return value;
    }
    function parse(raw) {
        if(typeof raw!=="string"){return raw;}
        if(raw.length>65536){return null;}
        try{return JSON.parse(raw);}catch(ignore){}
        // Only the documented array/object/string/number grammar is accepted.
        var pattern=/"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[A-Za-z_][A-Za-z0-9_]*|-?\d+(?:\.\d+)?|[{}\[\]:,]/g;
        var parts=[],match,last=0,token,depth=0;
        try{
            while((match=pattern.exec(raw))!==null){
                if(/\S/.test(raw.slice(last,match.index))){return null;}
                last=pattern.lastIndex;token=match[0];
                if(token==="["||token==="{"){depth+=1;if(depth>8){return null;}}
                if(token==="]"||token==="}"){depth-=1;}
                if(token.charAt(0)==="'"||token.charAt(0)==='"'){parts.push(JSON.stringify(decodeQuoted(token)));}
                else if(/^[A-Za-z_]/.test(token)){
                    if(/^(pid|lang|type|title)$/.test(token)&&/^\s*:/.test(raw.slice(last))){parts.push(JSON.stringify(token));}
                    else if(/^(true|false|null)$/.test(token)){parts.push(token);}else{return null;}
                }else{parts.push(token);}
            }
            if(/\S/.test(raw.slice(last))||depth!==0){return null;}
            return JSON.parse(parts.join(""));
        }catch(ignore){return null;}
    }
    function clean(value,limit){return typeof value==="string"?value.replace(/[\x00-\x1f\x7f]/g," ").slice(0,limit):"";}
    function tracks(raw) {
        var data=parse(raw),result=[],seen={},i,row,pid,lang,j;
        if(Object.prototype.toString.call(data)!=="[object Array]"){return result;}
        for(i=0;i<data.length&&i<128;i+=1){
            row=data[i];if(!row||typeof row!=="object"||!/^\d+$/.test(String(row.pid))){continue;}
            pid=Number(row.pid);if(pid>8191||seen[pid]){continue;}seen[pid]=true;
            lang=[];if(typeof row.lang==="string"){lang.push(clean(row.lang,32));}
            else if(Object.prototype.toString.call(row.lang)==="[object Array]"){for(j=0;j<row.lang.length&&j<2;j+=1){lang.push(clean(row.lang[j],32));}}
            result.push({pid:pid,lang:lang,title:clean(row.title,100),type:typeof row.type==="number"?row.type:0});
        }
        return result;
    }
    function label(track,index,audio) {
        var languages={por:"Português",pt:"Português",eng:"Inglês",en:"Inglês",spa:"Espanhol",es:"Espanhol",fra:"Francês",fre:"Francês",fr:"Francês",deu:"Alemão",ger:"Alemão",de:"Alemão",ita:"Italiano",it:"Italiano",jpn:"Japonês",ja:"Japonês",und:"Idioma não indicado"};
        var code=track.lang[0]||track.lang[1]||"",name=languages[code.toLowerCase()]||code||"Faixa "+(index+1);
        var codecs={1:"MP2",2:"MP3",3:"AC3",4:"AAC",5:"PCM",6:"OGG",7:"DTS",8:"EAC3"};
        if(track.title){name+=" · "+track.title;}if(audio&&codecs[track.type]){name+=" · "+codecs[track.type];}return name;
    }
    return {read:tracks,label:label};
}());
