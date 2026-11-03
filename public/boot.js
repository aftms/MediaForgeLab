/* Runs after the DOM exists: the MAG need not deliver window.onload. */
(function () {
    function message(value) {
        var node=document.getElementById("group");
        if(!node){return;}
        while(node.firstChild){node.removeChild(node.firstChild);}
        node.appendChild(document.createTextNode(value));
    }
    try {
        if(typeof MagPortal==="undefined") {
            message("Interface não carregada · Faça Restart portal (v6)");
            return;
        }
        MagPortal.init();
    } catch(ignore) {
        message("Erro ao iniciar a interface · Faça Restart portal (v6)");
    }
}());
