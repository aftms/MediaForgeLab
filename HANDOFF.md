# Media Forge Lab — continuidade

## Decisão atual do utilizador — 03/11/2026

Workspace próprio `D:\Workspace\MediaForgeLab`, projeto Gateway `mediaforgelab`.
A aplicação MAG/web/TV é a base. Antiga MediaCatalog arquivada em
`archive/legacy-20261103/`; não retomar automaticamente o roadmap antigo.
Evolução conjunta passo a passo, sem importar a interface antiga.

Nome visível **Media Forge Lab**, novo símbolo de enquadramentos/reprodução.
MAG r20, web v7, TV r8. Pesquisa TV com lupa apenas no topo direito, 30 títulos/página.
Favoritos, pastas, progresso, catálogo completo e atualização são partilhados.
Um único stream entre as interfaces; apps externas ao portal não são controladas.

Ver `TV.md` para SDKs e instalação e `WEB.md` para web/PWA. Segredos e catálogos
privados em `.runtime/` e `config.local.json`, nunca no Git.

Validação herdada: 61 testes Python; regressões MAG, TV ES5, recuperação de token
403, AVPlay e Chrome sintético. Samsung RTP1 imagem/som confirmados pelo utilizador;
arranque final 14,5 s. Xiaomi MiTV-MOOQ1 Android10 relógio nativo/HLS confirmados,
15,3 s; imagem/som ainda precisam de confirmação humana. Filmes/episódios nas TVs
precisam de teste físico. Todos os testes reais terminaram sem stream ativo.

Próximo passo: validar a nova identidade nas TVs e escolher com o utilizador a
primeira funcionalidade adicional da aplicação unificada. Não iniciar reescrita geral.

## Migração validada

Serviço e gestão ativos a partir desta raiz. HTTP MAG, TV, web e gestão deram
200; HTTPS validado com a CA existente. Hashes de catálogo, favoritos e progresso
iguais antes/depois. 61 testes Python e regressões JavaScript passaram nesta raiz.
WGT r7/1.0.7 e APK 1.1 assinados e instalados nas duas TVs. Entrada Admin
Media Forge Lab pertence agora a mediaforgelab; a antiga entrada URG está desativada.
O código antigo do portal foi retirado do Gateway, mantendo quatro BAT de
compatibilidade e o histórico Git. Ver ARCHITECTURE.md para a partilha de código.

## Web v6 — botão de instalação

Corrigido botão que só aparecia após beforeinstallprompt. Agora fica visível,
abre instalação nativa quando disponível ou ajuda contextual, distingue PWA
aberta/appinstalled e mantém ação após cancelar. Cache da shell atualizado;
manifesto corrigido para UTF-8. Testes Chrome isolado 1366/390px passaram,
JS syntax/diffcheck passaram; sem reinício do serviço nem acesso ao fornecedor.

## Portugal por defeito — MAG r20, web v7, TV r8

Entrar na secção TV seleciona PT em todas as interfaces. Filmes, séries e
favoritos mantêm-se sem filtro de país automático. Web/TV permitem trocar o
país no seletor; MAG abre as categorias de Portugal, BACK ou MENU → Países e
categorias permite escolher outro país. A pesquisa respeita o país selecionado.
Regressão MAG e compatibilidade ES5 passaram; Chrome verificou PT inicial,
ES selecionável, entrada/saída das secções e favoritos sem PT. Sem streams.
Samsung 1.0.8 instalada; Xiaomi recarrega a interface partilhada.

## Demora nos canais Xiaomi — APK 1.2

Fase concluída: proxy sem espera por blocos completos, preparação Android live
com análise 1 s/1,5 MB e HLS alvo 2 s; vídeo original, keyframes respeitados.
Diagnóstico de tempos sem segredos; keep-screen-on durante preparação nativa.
62 testes Python e regressões MAG/TV passaram; APK release 1.2 assinado,
instalado e aberto. Debug WebView desligado. Serviço atualizado e ativo.

Causa observada depende da variante: RTP1 HD 224/VODAFONE ~15–16 s e segmento
local com imagem preta; RTP1 HD 500/GENERALISTAS ~4,2–4,8 s e imagem normal
1080p no segmento. Parâmetros antigos no 500: ~5 s. Não afirmar melhoria de
15 para 4 s no mesmo stream. Ver TV.md para método/limites. Seleção automática
não alterada; categoria GENERALISTAS + HD permite escolher a alternativa.

Todos os testes reais sequenciais terminaram; lease livre, conta utilizável.
Próximo passo: utilizador confirmar som/imagem e tempo de abertura nesta versão
na Xiaomi. A fonte preta depende do fornecedor; sem pedido por correio, sem
thread associada. Não iniciar nova reprodução sem assegurar ausência de outros
leitores. Filmes/séries físicos e integração do legado continuam pendentes.
