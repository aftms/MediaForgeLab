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

## Demora web em filmes — web v8

Fase concluída e ativa: troca sequencial de pedidos Range da mesma sessão
FFmpeg, fechando cliente/origem anteriores antes de libertar a ligação única.
Elimina duas esperas de ~10 s observadas neste filme. HTTP/1.1 persistente para
GET/HEAD sem corpo evita resets/repetições de respostas grandes no Chrome;
POST/erros/corpos por ler fecham. Fila HTTP 64. Cache apenas de metadados VOD
por ID+URL (1 h/128 entradas), bypass no modo compatível; HLS web VOD alvo 2 s.
Etapas de preparação e duração desconhecida claras; avanço desativado durante
preparação; preservação de progresso e cancelamentos tardios testados.

Filme m2213260 (A Maravilhosa Árvore Encantada): preparação anterior ~24–26 s,
com falhas de entrega HTTP nas primeiras tentativas. Após correção, fotogramas
no Chrome em 4,06 s; nova retoma em 3,46 s. Imagem 1920×800 revista; vídeo original,
sem recompressão. Som não ouvido. Não generalizar os tempos a todos os títulos.
65 testes Python e regressões JS web/MAG/TV passaram. Ver WEB.md.

Testes reais autorizados terminados; lease livre. Utilizador pode voltar a
reproduzir. Próximo passo: Ctrl+F5 e confirmar a experiência no navegador habitual.
Sem bloqueios desta fase; pendentes anteriores de validação física TV/legado
mantêm-se. Não abrir outras transmissões usando a autorização já concluída.

## Filtro por origem — concluído

Web v9, TV r9, MAG r21; Samsung 1.0.9 instalada. Backend partilhado calcula
origin (VO/MEO/NOS/VIP/PT/OTHER); endpoint /api/catalog?view=origins&kind=tv
enumera antes de deduplicar. origin filtra antes de Auto e combina com pesquisa,
país/categoria/qualidade/favoritos. PT atual: MEO 223, PT 179, VIP 155, VO 120,
não indicada 99 entradas brutas. Sem remoção nem exclusão automática de VO.
MAG em Opções → Origem dos canais; web/TV no seletor superior. Filmes/séries
sem filtro; ao voltar a TV todas as origens. Identificação vem dos rótulos do
catálogo, não de análise técnica da origem do stream.

66 testes Python e regressões JS passaram. Chrome verificou seleção/pesquisa,
reset e visibilidade/encaixe web390px/TV1280×720. Corrigida instabilidade de dois
testes de rejeição: Windows pode encerrar com RST ao recusar corpo não lido;
a ausência de execução da ação continua verificada. Nenhuma alteração nesses
controlos de autorização em produção. Hashes de dados privados preservados.

Próximo passo: utilizador reabrir Xiaomi/Samsung, Ctrl+F5 na web ou Restart portal
na MAG e escolher origem. Sem bloqueios. Não foram iniciadas transmissões nem
alterados favoritos. Pendentes anteriores de validação física/legado mantêm-se.

## Categorias próprias de TV — concluído

Taxonomia local partilhada em channel_categories.py e catalog.py: Generalistas,
Desporto, Filmes, Séries e entretenimento, Infantis, Notícias, Documentários,
Música, Estilo de vida, Religião, Adultos, Outros. Nome reconhecido precede pistas
amplas do fornecedor; pistas adultas têm prioridade. Variantes da mesma família
partilham a classificação de maior confiança. Origem e qualidade continuam
separadas, com filtros antes da deduplicação. Grupos originais e aliases mantidos;
filmes/séries, IDs, favoritos e progresso sem migração. Classificação aproximada;
Outros evita adivinhar quando falta informação. Sem custos/API externa adicionais.

Serviço atualizado; web v9/TV r9/MAG r21 e pacotes instalados continuam válidos.
67 testes Python e regressões JS MAG/TV/web passaram. Chrome confirmou categorias
próprias e MEO + Desporto em web/TV, sem reprodução. Contagens reais PT Auto:
422 famílias, soma das categorias igual ao total; contagens por categoria também
coincidem com os resultados filtrados para todas as origens, MEO e VO.

Próximo passo: reabrir as interfaces (Ctrl+F5 na web) e avaliar a organização.
Corrigir regras centrais se o utilizador identificar canais mal classificados.
Sem bloqueios desta fase. Não foram abertas transmissões para estes testes.
Validações físicas anteriores/integração do legado continuam pendentes.

## Identidade MAG r22 — publicada

Utilizador reportou nome/logótipo antigos na MAG física. HTTP LAN8090 e loopback
já serviam Media Forge Lab r21 e o PNG atual (hash igual ao workspace), pelo
que a causa na box ainda não foi confirmada: aguarda revisão/Portal 1 URL.
MAG r22 usa o nome MediaForgeLab no cabeçalho/título/OSD, mesmo logótipo comum,
referências de CSS/JS/PNG v22 e meta no-cache para WebKit antigo. Retirada etiqueta
estática v6 da inicialização. Sem alteração a chaves de armazenamento ou leitura.

Navegação/regressões MAG passaram. Chrome1280×720 confirmou página LAN, nome,
logo carregado e r22, com lista real; sem streams nem reinício do servidor.
Próximo: Restart portal na MAG e confirmar r22. Se persistir identidade antiga,
verificar Portal 1 URL; URL atual com chave nova: http://192.168.1.240:8090/?v=22.
Não afirmar que cache é causa comprovada nem que o ecrã físico foi validado.

## Filtros de filmes/séries — web v10 / TV r10 / MAG r23

Concluído e ativo. País/idioma + género combinam com categoria, pesquisa e
favoritos no catálogo partilhado. Web/TV: seletores superiores; MAG: Opções →
Filtrar por país / idioma ou Filtrar por género. País é a versão do catálogo,
não país de produção. Não há predefinição PT nos filmes/séries; TV mantém PT.
Regras locais em vod_filters.py: géneros dos metadados, categorias como fallback,
desconhecidos explícitos; múltiplos géneros e grupos PT/BR sem duplicar títulos.

68 testes Python e regressões JS MAG/TV/web passaram, incluindo país+género+
pesquisa+categoria+favoritos e navegação dos seletores MAG pelo comando simulado.
Chrome confirmou resultados reais PT+Ação em filmes e séries nas interfaces web
+TV, 390px sem overflow e TV1280×720 com paginação visível. Filme PT: 6072 títulos,
206 classificados Ação; séries PT:708,197 Ação. Muitos filmes não têm metadados:
5063 PT ficaram em Sem género indicado. Sem custos/API extra/streams de teste.

Serviço reiniciado com lease idle; hashes de favoritos, layout, progresso e
snapshot iguais antes/depois. Samsung 1.0.10 assinada e instalada na .229; requer
reabrir app. Xiaomi mantém APK1.2 e recebe UIr10 hospedada ao reabrir. MAG Restart
portal r23; web Ctrl+F5 v10. Validação com comando físico ainda por confirmar.
Sem bloqueios desta fase; validações físicas anteriores/legado continuam pendentes.

## Sobre na web — v11 concluída

Botão Sobre com ícone e Web v11 sempre visível no menu. Diálogo acessível com
MediaForgeLab, logótipo, versão da interface efetivamente carregada (constante
WEB_VERSION no JS) e modo Navegador/PWA. Recursos/cache web v11. Menu lateral
rolável em janelas baixas. Sem alterações de backend, MAG, TV ou dados privados.

Regressões web-player passaram. Chrome1280×720 e390×844: nome/logo/versão,
abertura, fecho no botão e Escape, retorno de foco e ausência de overflow
confirmados; capturas revistas. Modo PWA deriva de display-mode/standalone;
não foi feita nova instalação Android. Sem transmissões nem restart do serviço.
Próximo: Ctrl+F5 ou reabrir PWA e escolher Sobre. Sem bloqueios desta fase.

## Ajuda de instalação — web v12

Utilizador não encontra opção de instalação no menu do navegador (captura do
fallback). Pergunta pendente: navegador, Windows/Android e endereço usado.
Chrome isolado loopback8091: sem erros de installability/manifest, SW activated
com controller. Causa no dispositivo do utilizador ainda não confirmada.

Substituídas instruções genéricas por passos Chrome Windows, Edge Windows e Chrome
Android; secção provável abre automaticamente, todas consultáveis. Referências
oficiais Google/Microsoft confirmadas e ligadas no diálogo. Web/cachev12.
Regressão web-player passou; Chrome com UA Chrome/Edge/Android verificou a seleção
de instruções e encaixe1280×720/390×844. Sem instalação real, streams ou restart.
Próximo: utilizador Ctrl+F5 e seguir submenu do navegador; se não existir, obter
navegador/endereço para diagnóstico do caso real. Sem bloqueio da alteração de UI.

## Biblioteca pessoal OneDrive — piloto preparado (2026-11-03)

Implementação autorizada pelo utilizador para TODAS as interfaces. Web v13,
TV r11/Samsung 1.0.11, Xiaomi APK 1.3 e MAG r24. Interface ES5 comum em
public/tv/personal.*, web sob /web/personal/ para permanecer na PWA. OneDrive
pessoal read-only Files.Read/offline_access, device code, DPAPI Windows. SQLite
transacional com pastas explicitamente escolhidas, IDs drive/item, favoritos,
álbuns e progresso comuns. Atualização não descarrega vídeos. Imagens limitadas
a 400 ficheiros/128MB; streaming progressivo via pipeline HLS comum, remux quando
compatível e adaptação até1080p, cache temporário limpo ao parar. Uma reprodução
pessoal de cada vez, independente da única reprodução IPTV. Originais intactos.

76 testes Python e regressões JS MAG/TV/web passaram. Chrome isolado confirmou
vídeo sintético HLS com imagem, pausa/retomar, avanço, fim com completed persistido;
fotografias/galeria com15itens atravessando páginas, álbuns/favoritos comuns,
pesquisa,390px e navegação simulada do comando/MagTV Android. Testes incluem
atualização sem duplicados, falha/vazio/cTag instável/paginação repetida, DPAPI,
CSRF/Origin/rotas privadas, leases independentes, remux/transcode e limpeza.
Os últimos aliases PWA/ponte Android também passaram no Chrome. Não abriram
streams reais de IPTV nem conteúdos da conta Microsoft.

Serviço reiniciado só com lease IPTV idle e refresh parado; hashes de favoritos,
progresso/snapshot iguais. HTTP loopback8091 e LAN8090 validados com
OneDrive desligado. Samsung1.0.11 e Android1.3 compilados, assinados e instalados
nas TVs .229/.90 sem iniciar reprodução. Reabrir apps; MAG Restart portal r24;
web Ctrl+F5/reabrir PWA v13. Sessões sintéticas encerradas.

BLOQUEIO EXTERNO: não foi fornecido Application/Client ID. Utilizador disse ter
um ID e confirmou OneDrive pessoal, mas perguntou se Entra é pago (tem365pessoal).
Esclarecido: EntraFree existe, P1/P2 desnecessários; criação do registo pede conta
Azure/subscrição ativa e diretório, podendo usar conta gratuita; 365pessoal não
substitui registo técnico. Não foram criados registo/serviços Azure nem iniciado
autorização. Pergunta pendente: consegue abrir Registos de aplicações no Entra,
ou aparece erro/pedido de conta Azure? Não repetir pedidos de segredos. Pedir
apenas GUID público/ajudar configuração. Não usar IDs públicos de apps alheias.

Próximo: concluir registo próprio e auth por device code, escolher UMA pasta
piloto com o utilizador, testar metadados/imagem/vídeo reais e depois validar
comandos/reprodução nas TVs e MAG físicos. Não declarar OneDrive ou hardware
validados pelos testes sintéticos. UI de seleção de pastas foi testada com mocks;
Graph real e capacidade de duas adaptações simultâneas permanecem por confirmar.
HEIC/RAW dependem das miniaturas; atalhos remoteItem ignorados; sem IA, alterações
ou eliminação de originais. Configuração, limites e testes em PERSONAL.md.

## Registo Microsoft configurado — autorização pendente (2026-11-03)

Utilizador concluiu o registo MediaForgeLab para contas Microsoft pessoais,
ativou public client flows e confirmou permissões delegadas Files.Read e
Files.Read.All. A permissão adicional foi explicitamente pedida pelo utilizador
para ficar preparada desde já. Código pede ambos os scopes + offline_access,
sem escrita. Client ID da captura configurado apenas em .runtime/personal;
tenant consumers. O bloqueio anterior de acesso ao Entra está ultrapassado.

7 testes pessoais passaram. Serviço reiniciado com IPTV/pessoal idle e scans
parados. Microsoft aceitou o pedido device code; aguarda consentimento do
utilizador. Código temporário e tokens não foram registados no handoff/Git.
Abrir http://127.0.0.1:8091/web/personal/?client=web para ver o código/endereço.
Se expirar, Ligar OneDrive gera outro. Próximo: autorizar na Microsoft, confirmar
ligação e escolher UMA pasta piloto antes de indexar. Graph real e reprodução
física continuam por validar; nenhuma transmissão foi iniciada nesta fase.

## Favicon da página Pessoal — corrigido (2026-11-03)

A página principal web já declarava um favicon, mas Pessoal não tinha link icon.
Adicionada referência explícita ao brand.png existente, relativa para funcionar
em /web/personal/ e /tv/personal.html, com tipo image/png e chave v1. Ativa sem
reiniciar serviço. Verificados HTML e PNG HTTP200/type/assinatura em loopback8091
e LAN8090 nas páginas principal e Pessoal. Ctrl+F5 no Chrome para recarregar.
Sem alteração de código do leitor/catálogos. Pacotes de TV não reinstalados por
esta alteração exclusiva do separador do navegador. Não foi validado o separador
na sessão física do Chrome do utilizador; apenas HTML/HTTP.

Continuidade OneDrive: consentimento concluído e connected=true confirmado na
fase anterior, sem erros; ainda aguardava escolha de pasta piloto. Próximo passo
funcional mantém-se: escolher uma pasta pequena e validar conteúdos reais.

## Fotografias OneDrive reais — correção ativa (2026-11-03)

Utilizador indexou pasta piloto:18fotografias/1vídeo; reportou fotografia sem
imagem. Diagnóstico real: $select=id,@microsoft.graph.downloadUrl devolvia só id;
GET do item sem $select devolveu annotation válida. Conteúdo usa
my.microsoftpersonalcontent.com e miniaturas francecentral1-mediap.svc.ms, ausentes
da allowlist. Retirado $select desse pedido e acrescentados microsoftpersonalcontent.com
+svc.ms com validação HTTPS443/fronteira de domínio/sem userinfo, incluindo redirects.
URLs assinados e tokens nunca impressos/registados. Sem alteração de permissões.

8 testes pessoais passaram, incluindo regressões de annotation omitida, domínios
Microsoft, hosts lookalike rejeitados e ausência de bearer em pedidos binários.
Fotografia reportada obtida realmente, miniaturaJPEG178x240 e inteira801x1080.
Serviço reiniciado apenas idle/scan parado; fingerprint lógico de items/roots/
membership/albums/album_items igual antes/depois; conta continua ligada.
Chrome isolado confirmou duas fotografias descodificadas sem erro; sem screenshots
ou exportação de conteúdo pessoal. Correção backend beneficia todas as interfaces,
sem reinstalar pacotes TV. Fechar/reabrir foto; Ctrl+F5 se necessário.

Primeiro teste Chrome selecionou o primeiro item geral, que era o vídeo, e falhou
por esperar uma imagem. Vídeo pessoal iniciou pipeline HLS (ready,2segmentos
servidos), depois encerrado ao fechar navegador; estado idle confirmado. Não
confundir com validação visual/áudio de vídeo. Teste ajustado explicitamente a
Fotografias e passou. Nenhum stream IPTV iniciado. Progresso do vídeo pode ter
sido registado pelo leitor; não reposto sem evidência do valor anterior.

Próximo: aceitação das fotos pelo utilizador; vídeo com imagem/som e reprodução
nas TVs/MAG físicos ainda por validar. Sem bloqueio da fotografia reportada.

## MP4 pessoal no Chrome — Pessoal v2 (2026-11-03)

Reprodução real do MP4 piloto reproduziu o problema: servidor prepara em poucos
segundos, Chrome declara canPlayType HLS=maybe mas o leitor nativo emite error4
logo após loadedmetadata/playing; currentTime fica0. Interface ignorava onerror e
continuava a mostrar formato adaptado. Correção: HLS.js/MSE já incluído passa a
ter prioridade, fallback HLS nativo se MSE indisponível, erros explícitos e guardas
contra callbacks depois de fechar/cancelar. JS ES5, sem alterar adaptadores nativos
MAG/Samsung/Android. Página/JS Pessoal v2; ativa sem restart/backend ou reinstalar
TVs, pois esta correção aplica-se ao leitor de navegador.

Teste real Chrome isolado com clique de rato: primeiro avanço de vídeo cerca de
4,5s após escolher; 848x478, readyState4, currentTime avançou até17,6s e evento ended
sem erro (duração17,8s). Pipeline remux, sem recompressão; sem captura/exportação de
conteúdo pessoal nem streams IPTV. Ligação pessoal idle no fim; o vídeo pode agora
estar marcado concluído por ter chegado ao fim no teste. Som audível não verificado.
Novo teste JS cobre prioridade MSE mesmo com native=maybe, fallback, erro explícito,
cancelamento e manifest tardio. Regressões web-player e tv-player passaram.

Próximo: utilizador Ctrl+F5 na página Pessoal (v2), abrir o MP4 e confirmar imagem/
som. Aceitação nas TVs/MAG continua pendente; sem bloqueio conhecido no Chrome.

## Barra de posição pessoal — Pessoal v3 / TV r12 (2026-11-03)

Pedido: escolher o ponto do vídeo com slider. Implementado na interface pessoal
ES5 comum web/PWA, MAG e TVs. Barra com tempo atual/total, preview ao arrastar,
um pedido apenas ao confirmar/largar; comando ←/→ escolhe em segundos e OK
confirma. BACK cancela seleção, cima/baixo regressa aos controlos. Integração
MagTV.remote evita abrir teclado Android ao confirmar a barra. Mantém pausa se
alterada durante pausa, desativa enquanto prepara/sem duração e limita ao fim.
Usa o mecanismo existente de reinício HLS na posição, sem SetPosTime nativo MAG.
Limpa temporizadores ao fechar/reiniciar. Fundo preto no vídeo web e contador
único; barra mantém-se visível enquanto tem foco/seleção.

Testes JS novos: preview sem requests, commit único, clamp/arredondamento de
segundos, cancelamento, pausa e duração desconhecida/preparing. Regressões de
leitores pessoal/web/TV e navegação/API MAG/TV passaram. Chrome com vídeo sintético
verificou reprodução após mudar posição, arrastar sem múltiplos pedidos,
setas/OK/BACK pela ponte Android, pausa preservada e libertação da sessão.
Capturas1280x720/390x844 revistas. Uma repetição ultrapassou35s a aguardar vídeo;
repetição com diagnóstico passou, mostrando demora no processamento/ranges do
pipeline sintético, não pedidos repetidos da barra. Não prometer seek instantâneo;
o novo ponto precisa de preparação pelo servidor. Reprodução física ainda pendente.

Ativo sem restart do backend; reprodução pessoal em curso no navegador do
utilizador não foi interrompida. Samsung1.0.12/r12 compilada/assinada/instalada,
com guarda contra instalação durante reprodução Samsung. Xiaomi APK1.3 recebe
interface hospedada r12 ao reabrir; MAG entrar novamente em Pessoal (v3).
Nenhum stream IPTV ou vídeo pessoal aberto nesta fase: só servidor sintético,
encerrado no fim. Testes não comprovam funcionamento do slider em hardware físico.
Próximo: Ctrl+F5 na web, Pessoal v3, experimentar arrastar; aceitar nas TVs/MAG.


## Navegação Pessoal na MAG — r25 / Pessoal v4 / TV r13 (2026-11-03)

Pedido: Pessoal incoerente/espremido no menu MAG, sem destaque de seleção;
setas nos conteúdos saltavam entre ações de favorito/álbum. Causa: botão
Pessoal absoluto fora de #navigation, excluído do CSS remote-focus; navegação
pessoal geométrica incluía todos os botões dos cartões e navegação espacial
nativa MAG não era desativada até iniciar vídeo.

Integrado Pessoal como quinta nav-tab com ícone/descrição/espaçamento e foco
dourado. Grelha pessoal usa linhas/colunas dos cartões, exclui ações secundárias
do percurso de setas e destaca cartão/título. Opções do item via MENU/INFO ou
botão acima da grelha, sem botões de cores; favoritos/álbuns mantêm ações por
rato/toque. Diálogos aninhados preservam retorno; favorita mantém seleção após
recarregar dados. Navegação espacial MAG desativada logo ao entrar no Pessoal.

Validação: node --check; navigation.cjs, personal-timeline.cjs,
personal-player.cjs, tv-player.cjs, tv-api.cjs e web-player.cjs PASS.
Novo personal-navigation-browser.cjs PASS em Chrome com dados sintéticos a
1280x720, 1920x1080 e 390x844: setas saltam ações, opções/álbum, mutação de
favorito preserva foco, destaque/alinhamento do menu MAG por teclas reais CDP.
Capturas revistas. Nenhum conteúdo pessoal real nem stream IPTV aberto.

Estáticos ativos sem reiniciar backend. Samsung1.0.13 assinada/instalada após
confirmar ambas as sessões de reprodução inativas. Xiaomi APK1.3 carrega TVr13
hospedada ao reabrir. MAG Restart portal para r25 e Pessoal v4. Testes no PC
não confirmam o comando/hardware MAG: falta aceitação física pelo utilizador.
Próximo: confirmar navegação natural entre conteúdos na MAG. Restante plano
OneDrive mantém piloto e validação de reprodução nas TVs/MAG pendente.


## Áudio e legendas — web v14 / Pessoal v5 / TV r14 (2026-11-03)

Pedido: tornar áudio/legendas disponíveis na web. Implementado componente ES5
public/tv/track-controls.* comum à web IPTV, TVs e Pessoal (incluindo MAG).
Painel sempre identificável: áudio único/ausente, idiomas, desligar legendas,
faixas incompatíveis desativadas. Expandido na web IPTV, compacto nas TVs/Pessoal.
OK/setas/OK confirma seleção por comando, BACK cancela; controlos não desaparecem
com foco. Troca preserva posição; em pausa guarda escolha sem iniciar stream.
MAG IPTV mantém opções nativas existentes (sem alterar a solução de seek).

Backend MediaManager identifica áudio/subtítulos; aceita subtitle=-1/off ou
índice. Mesmo FFmpeg/demuxer/origem produz HLS e WebVTT progressivo em ficheiro
privado temporário, sem segunda ligação nem recompressão só por ativar legendas.
Pulse devolve cues completos de uma cauda limitada262KB/1000cues, com validação
de token/IP e texto simples. Última legenda termina em newline simples (FFmpeg)
e é lida corretamente. Suporta subrip/srt/ass/ssa/webvtt/mov_text/text; PGS/DVD/DVB
não suportados/indicados. Não procura legendas externas nem gera tradução.
Chrome usa TextTrack/VTTCue para fullscreen; TVs nativas usam overlay com relógio
local. Trocas/stop removem cues, callbacks de pulse tardios não apagam sessão nova.

Testes: test_tracks.py2/2 (FFmpeg real; AAC880Hz escolhido, PT/EN, seek10s,
remux, off, limpeza, exclusão entre dispositivos e input inválido preserva lease),
test_media7/7, test_media_pipeline3/3; regressões JS web/MAG/TV/API/Pessoal/slider
PASS. Chrome sintético: texto PT/EN efetivamente visível, pausa+mudança sem lease,
retoma, desligar, comando e casos sem suporte, vídeo pessoal390px; capturas revistas.
Nenhum vídeo pessoal real ou fornecedor aberto nesta fase. Aceitação física
TV/MAG e faixas concretas do fornecedor permanecem pendentes.

Ativação: esperou pela catalogação OneDrive em curso, que terminou com31144
itens vistos (31125 novos,19 atualizados), sem erro. Reinício controlado apenas
após ambas as reproduções idle, scan/refresh parados. Rotas dos novos assets e
aliases PWA HTTP200. Samsung1.0.14/r14 assinada/instalada sem reprodução Samsung;
Xiaomi APK1.3 carrega UI hospedada; MAG rootr25 mantém-se, Pessoalv5. Web Ctrl+F5
para v14. Próximo: utilizador confirmar idiomas/legendas no filme e nos dispositivos.


## Janela do leitor web / duplo clique — web v15 (2026-11-03)

Utilizador reportou demora ao maximizar, confirmou depois que o botão nativo
no vídeo funciona bem mas duplo clique não. Preservar os controlos nativos que
apreciou (som, pausa, fullscreen, menu). Adicionados −/＋ e ⛶ no cabeçalho,
resize:both no computador e limites responsivos; são só alterações de layout.
Fullscreen CSS elimina limite58vh. Duplo clique na imagem partilha função
fullscreen com botão e restaura reprodução se o primeiro clique provocou pausa;
se já estava pausado, continua pausado. Faixa inferior80px dos controlos nativos
excluída. Escape/fullscreenchange não deve acionar fecho do diálogo.

Antes qualquer pausa libertava imediatamente a sessão após guardar progresso.
Agora confirmação900ms com epoch/geração/token evita libertar ligação por pausa
transitória; play cancela, resize/fullscreen reavaliam. Pausa persistente continua
a libertar; mudar tamanho não retoma vídeo pausado. Fecho/start cancelam timers.
Causa do duplo clique no dispositivo do utilizador não foi observada diretamente;
Chrome sintético valida proteção e comportamento novo sem abrir fornecedor.

Testes: web-player.cjs PASS; web-window-browser.cjs PASS com FFmpeg sintético
real e Chrome: botões −/＋, drag real do canto, requestFullscreen e duplo clique
real entra/sai, resize viewport, pausa transitória sem novos pedidos web/stop,
pausa persistente liberta, duplo clique em pausa preserva pausa, ajuste em pausa
não abre stream,390px sem overflow. Captura revista. Estáticos ativos sem reiniciar
backend nem interromper o canal que o utilizador tem aberto. TVs/MAG/Pessoal
mantêm versões anteriores, esta alteração é específica da janela web solicitada.
Próximo: Ctrl+F5 para webv15 e confirmar duplo clique no computador do utilizador.

Ajuste final: duplo clique usa estado fullscreen capturado no primeiro clique;
se o navegador já realizou a transição, não envia um segundo pedido. Teste final
confirma ausência de aviso indevido de fullscreen e mantém todos os checks acima.


## Painel de idiomas discreto — webv16 / TVr15 / Pessoalv6 (2026-11-03)

Utilizador achou painel Áudio e legendas intrusivo/forte. Componente partilhado
fecha por defeito em todas as interfaces e em reset/novo conteúdo. Eliminados
fundo/moldura, título menor de peso normal e cor neutra; seletores compactos220px,
labels leves, nota pequena, foco acessível mantido. Não altera reprodução.
Verificação visual Chrome com componente e dados sintéticos: fechado baixo70px,
abrir seletores, reset fecha,390px sem overflow; capturas fechado/aberto revistas.
JS syntax e diff check PASS. Sem streams abertos nem restart backend. Samsung
1.0.15 assinada/instalada após verificar ausência de reprodução Samsung. Xiaomi
hospedada recebe r15; MAG rootr25 mantém-se, Pessoalv6. Web Ctrl+F5 parav16.
Próximo: aceitar apresentação discreta; testes físicos anteriores continuam pendentes.


## Janela sempre à frente — webv17 (2026-11-03)

Pedido Windows: destacar vídeo sobre outras apps. Botão Destacar/Repor usa
Picture-in-Picture nativo Chrome no mesmo elemento/sessão; deteta suporte,
aguarda loadeddata, atualiza enter/leave, fecha PiP explicitamente ao fechar
leitor. Não copia vídeo nem abre stream adicional. CSS pequeno no cabeçalho.
Teste real Chrome sintético web-pip-browser.cjs PASS: enter/exit, avanço do
relógio sem novo start/stop, destaque durante pausa não retoma e fecho sai PiP.
web-player regressão PASS. Posição física always-on-top/mover/redimensionar
entre apps Windows requer confirmação utilizador. Sem restart/backend/fornecedor.

Durante teste o utilizador ouviu tom semelhante a beep: vídeo sintético tinha
sine440Hz e Chrome não estava mudo. Assumida responsabilidade, servidor e
browser isolados imediatamente fechados. Repetição concluída com --mute-audio
E video.muted=true. TODOS os testes de vídeo futuros devem usar ambas as
proteções; não emitir áudio sintético. Nunca fechar browser pessoal do utilizador.
Próximo: Ctrl+F5 webv17, reproduzir, botão Destacar; manter separador aberto.
TV/MAG/Pessoal não alterados nesta funcionalidade específica do Windows web.


## Origem preserva categoria — webv18 / MAGr26 / TVr16 (2026-11-03)

Pedido: mudar combo Origem não deve mexer na combo Categoria. Web e TV deixam
de limpar state.group e de reconstruir filtros ao alterar/limpar origem.
Listagem de categorias independente da origem, mantendo opções estáveis; pesquisa
de itens continua a combinar categoria+origem, incluindo resultado vazio sem
reset. MAG originPicker também preserva categoria atual. Mudança de país mantém
reset dependente existente. Sem alteração de backend/catálogo/reprodução.

Testes origin-category.cjs web/TV: MEO, NOWO, todas preservam valor/opções,
paginação reinicia; país continua a limpar. navigation.cjs regressões + teste
MAG com categoria Desporto e origem MEO PASS. JS syntax/diff check PASS.
Nenhum stream/áudio aberto. Estáticos ativos sem restart. Samsung1.0.16
assinada/instalada após guarda de reprodução; Xiaomi hospedada TVr16. Pessoalv6
inalterado. Próximo: Ctrl+F5 webv18; MAG Restart portalr26 se necessário.


## Lista ativa dentro do leitor web — webv19 (2026-11-03)

Pedido no leitor web: selecionar diretamente outro canal/filme e Anterior/Seguinte.
Barra compacta acima do vídeo com botões, seletor e posição/total. Contexto de
filtros/secção/pasta fica capturado ao abrir; metadados paginados sob pedido,
sem descarregar catálogo inteiro. Seletor permite navegar páginas sem reproduzir;
adjacentes atravessam páginas automaticamente. Suporta tv/movie/episode,
favoritos e continuar a ver. Mantém categorias/origens/qualidade/pesquisa/ordem.
Troca usa stop antes de start, guarda progresso, bloqueia reentrância durante
preparação; fechar invalida resposta tardia e não deixa play em espera reabrir.
Backend e interfaces TV/MAG/Pessoal não alterados nesta melhoria do leitor web.

Testes playback-list.cjs: filtros capturados, paginação, seleção direta, limites,
busy, falha preserva seleção, resposta tardia descartada e pasta favoritos PASS.
web-player.cjs e origin-category.cjs regressões PASS. Chrome sintético silencioso
(--mute-audio e video.muted=true):61 filmes, próximo/anterior entre páginas,
paginar sem iniciar stream, seleção direta, stop antes de cada start, limites,
largura390px e libertação ao fechar; reprodução inicial e após última troca.
Sem fornecedor/ficheiros reais, sem restart backend; estáticos webv19 confirmados.
Próximo: Ctrl+F5 e experimentar a lista acima do vídeo; aceitação pelo utilizador.


## Preferência de áudio PT-PT / inglês — webv20 / TVr17 / MAGr27 (2026-11-03)

Pedido: filmes e episódios abrem em PT-PT quando explicitamente identificado;
caso contrário inglês, depois faixa original/default. Português genérico não
assumido como europeu. Web/TV enviam audio=auto na abertura, backend seleciona
com metadados do probe existente; índice efetivo fica numérico para preservar
alteração manual em pausa/retoma/seek/compatibilidade. Sem alteração na TV em
direto, pessoais, legendas, catálogo ou filtros. MAG seleciona PID em timer fora
dos callbacks nativos, com retries limitados para descritores atrasados; cancela
ao fechar/trocar e nunca reaplica após escolha manual ou eventos de seek.

Testes: fixtures de idiomas comuns a Python/MAG, origem default, unidade media,
navigation (callback diferido, escolha manual, stop, TV), regressões web/lista/
origem/TV PASS. Pipeline FFmpeg sintético confirmou faixa inglesa pelo áudio
descodificado, sem saída audível; só um input e uma lease, inválidos preservam
sessão. Chrome --mute-audio + video.muted=true: vídeo real local começa em inglês,
alteração manual para português preservada após pausa/retoma, reabrir repõe inglês,
fechar liberta sessão. Sem streams do fornecedor. Aceitação em hardware pendente.
Ativação concluída: utilizador confirmou fecho do leitor; guarda de playback/scan/refresh
verificou idle, backend reiniciado. HTTP webv20/MAGr27/TVr17 confirmado. Samsung
1.0.17 instalada (exit 0); Xiaomi recebe UI hospedada ao reabrir. Pessoalv6 inalterado.
Próximo: Ctrl+F5 web / reabrir TVs / Restart portal MAG; confirmar em dispositivos físicos.


## Barra de posição integrada no vídeo — webv21 (2026-11-03)

Pedido: usar slider dentro do vídeo em vez do externo. HLS atual apresenta apenas
janela preparada, por isso duração nativa não representa filme inteiro. Solução:
barra VOD única no video-stage com range duração/posição completas, pausa/play,
volume/mute e fullscreen do wrapper. VOD desativa controls nativos parciais;
TV em direto mantém controls nativos. Barra auto-oculta, permanece em pausa/foco,
responsiva390px e em fullscreen. Header/PiP/redimensionamento preservados.
Sem mudança do backend/formato/HLS nem nova ligação para obter duração.

Seek mantém pipeline existente e áudio/legendas; guarda de reentrância e geração
cancela resposta tardia quando fecha. Paused seek não abre stream, retoma no ponto
escolhido e guarda posição ao fechar. Botões +/-30 usam posição escolhida em pausa.
Native PiP continua suportado mas a barra completa pertence à página; a janela
PiP mantém controlos nativos do browser. MAGr27/TVr17/Samsung1.0.17/Pessoalv6 iguais.

Testes: unidade preparação/cancelamento, seek duplo e close durante save, paused
seek sem stream e posição persistida PASS; regressões lista/origem PASS. Chrome
sintético120s, --mute-audio e video.muted=true: barra120s com buffer<60, click real
~90s, recuo8s, inglês mantido, pausa/seek60/resume, fullscreen/seek30,390px e lease
libertada PASS. Screenshot móvel inspecionado. Testes reais Chrome fullscreen
botão/duplo-clique/resize e PiP sem novas sessões PASS. Sem fornecedor, ficheiros
pessoais ou reinício backend. Estáticos webv21 ativos; aceitação física pendente.
Próximo: Ctrl+F5 e usar a barra dentro do vídeo; pode haver preparação ao saltar.


## Ícone Pessoal — webv22 / MAGr28 / TVr18 (2026-11-03)

Substituído glifo ▧ na web/TV e pasta genérica na MAG por álbum de fotografias
sobrepostas, traço verde-água e sol dourado. Geometria em design-assets.py usa o
mesmo sistema de ícones; PNG64 transparente suporta MAG antiga. Web/MAG usam
assets/personal.png; cópia idêntica personal-icon.png no pacote/hospedagem TV,
gerada pela mesma função. Web alinha ícone/texto como restantes entradas.

Verificado PNG RGBA64, igualdade de bytes entre variantes, conteúdo do WGT,
HTTP das duas imagens, sintaxe JS e diff. Pré-visualização estática Chrome
inspecionada. Sem streams. Servidor mantém tabela estática em memória: reiniciado
apenas após confirmar todas leases/scan/refresh idle, para registar novos PNG.
Samsung1.0.18 instalada exit0; Xiaomi recebe UI hospedada ao reabrir. Pessoalv6
inalterado. Próximo Ctrl+F5/reabrir TVs/Restart portal MAG. Sem bloqueios.


## Falsa pausa ao abrir — webv23 (2026-11-03)

Utilizador reportou e confirmou «Em pausa · ligação libertada» espontâneo ao abrir,
com vídeo parado a0s. Reproduzido: schedulePauseRelease tratava video.paused inicial
como pausa após ready/start, inclusive resize/evento pause antes do primeiro playing.
Timer900ms libertava lease prematuramente. Novo playbackStarted só arma após evento
playing válido, reset em detach; pausa de arranque/resize não liberta nem grava posição.
Pausa após reprodução continua com900ms, guards de geração/sessão/epoch mantidos.

attemptPlayback aplica guardas a callbacks/promessas tardias e distingue rejeição
de autoplay: mensagem «O navegador bloqueou a reprodução automática. Prima ▶ para
iniciar», guarda posição inicial/resume, liberta ligação sem sobrescrever progresso.
Outros erros de arranque têm mensagem própria. ▶ reabre normalmente após gesto.

Testes: reprodução da falha antes da alteração; web-pause-lifecycle unidade com
startup, playing, pausa real/transitória, late pause/start, autoplay e posição PASS.
web-player regressões PASS. Chrome --mute-audio + video.muted=true com canal/filme
sintéticos: arranque retardado sob resize/pause continua com mesma sessão; imagem,
pausa real liberta; autoplay negado mostra mensagem certa/liberta, ▶ retoma e fechar
liberta PASS. Nenhum acesso ao fornecedor. Backend/TV/MAG/Pessoal inalterados.
Estáticos webv23 ativos, sem restart. Próximo Ctrl+F5 e reabrir conteúdo; utilizador
confirma arranque real. Sem bloqueios. Nunca executar testes com áudio audível.


## Coleções v1 — web24 / MAGr29 / TVr19 (2026-11-03)

Utilizador aceitou nome Coleções e autorizou implementação do módulo de vídeos
sociais, comum a todas as versões. Código/uso/limites em COLLECTIONS.md.
SQLite privada partilhada, categorias/subcategorias, pesquisa/origem/favoritos,
listas ordenadas até500 entradas, progressos por ocorrência, retoma e importação
transacional até100 links. Canonicalização por IDs conhecidos, sem scraping/download.
YouTube/Vimeo oficiais com eventos de fim; Facebook público manual; outros links
abrem na origem na web. Leitor externo isolado, sem chaveTV/fornecedor; APIs protegidas.
Android1.4 usa WebView separada sem ponte Java para Coleções.

88 testes Python PASS; regressões MAG navegação, TVAPI/AVPlay e origem PASS.
Chrome real silencioso: YouTube playing/time, pause/resume, seek ao fim e próximo
automático PASS; CRUD/favoritos/pesquisa/teclado/layouts web390/1280,TV1920,MAG1280 PASS.
Samsung física .229 autorizada pelo utilizador: WGT1.0.19 instalada, YouTube real
sem som, time advancing/pause/resume, navegação/teclado/Voltar PASS. Item de teste
removido e leitor fechado; deixou Coleções vazia. Screenshot debugger sem resposta,
teste interrompido e limpeza confirmada por segunda ligação CDP; não repetir captura.

Backend ativado após guarda idle provider/personal/scan/refresh; novos routesHTTP200.
Web24, MAGr29 e TVr19 ativos. APK Android1.4 construído/assinado, NÃO instalado:
utilizador desligou Xiaomi .90 e pediu apenas teste Samsung. Não contactar/ligar
Xiaomi até disponível. MAG física, Facebook e Vimeo reais ainda por confirmar.
Restante IPTV/Pessoal e exclusão de conta fornecedor preservados; testes sem IPTV.

Importação automática HealthForgeLab bloqueada por ausência de concessão API:
resource_access.api_services=[] no projeto mediaforgelab. Não contornar com outra
identidade. Alternativa disponível: importar exportação JSON/links do utilizador.
Nenhum pedido de permissão/melhoria foi enviado; API existente precisa de grant
antes de integrar. Próximo: utilizador experimentar guardar links e organizar
categorias/listas; instalar APK1.4 quando Xiaomi estiver ligada; validar vídeos
concretos nas plataformas que ainda não têm prova física. Não produzir áudio em testes.


### Pedidos durante a implementação — Coleções v2

Utilizador pediu Destacar na web, perguntou pelos títulos genéricos e pediu etiquetas.
Implementado: etiquetas partilhadas até20/vídeo, entrada por vírgulas no editor,
chips e filtro reutilizável, pesquisa, dedup Unicode/case/acento e JSONimport tags.
Categorias continuam independentes. Nomes YouTube/Vimeo via oEmbed oficial em fila
de fundo após importação/arranque, sem bloquear UI ou sobrescrever títulos manuais;
preview manual no editor. Verificação real:6 YouTube já com títulos/autor;1Facebook
com título genérico, indicação para editar manualmente. Não renomear Facebook por
adivinhação nem usar scraping/credenciais de outras apps.

Destacar web: PiP nativo para vídeo direto; Document PiP para embed. Só um leitor,
mesmo iframe adotado pela janela (browser recarrega; retoma posição conhecida).
Canal/origem/source verificados; wrapper aceita controlador same-origin opener
apenas no contexto PiP marcado. Fechar/retornar restaura DOM e encerra janela.
Requer Chrome/Edge compatível em localhost/HTTPS; não prometer PiP em HTTP LAN.
Facebook pode recomeçar porque não dá posição. TV/MAG não mostram Destacar.

10 testes Coleções e bateria91/91 PASS. Uma corrida de pipelinePessoal durantebuild
falhou; isolado PASS, repetição completa sembuild PASS. Sem alteração do pipeline.
Chrome real mudo: YouTube PiP/time/pause/resume/restore, MP4 nativo sem nova fonte,
tags UI normalizadas/filtradas e fecho de popup/iframe PASS. Docs COLLECTIONS.md.
Serviço reiniciado com guardas idle e títulos reais confirmados. Versão módulo2,
web24/MAGr29, TVr20/Samsung1.0.20; APK1.4 final construído e Xiaomi continua pendente.
Próximo: Ctrl+F5 em Coleções, usar Opções/Editar para etiquetas e título Facebook;
testar Destacar no PC; instalar APK1.4 quando Xiaomi voltar a estar ligada.


Fecho da fase: teste real Chrome adicional PASS para destacar em pausa, conservar
posição e fechar a janela PiP pelo próprio X, restaurando o leitor na página.
Samsung1.0.20 final reconstruída/instalada após os últimos ajustes. No futuro,
não testar novamente vídeos reais sem respeitar autorização e silêncio.

Última pergunta do utilizador: faz sentido etiquetas/subetiquetas nível2/3?
Respondido como proposta, NÃO implementada nesta fase: grupos até3níveis
(Atividade→Workout→Mobilidade/Força/Cardio; Zona muscular→Pernas→Gémeos/Glúteos;
Culinária→Tipo de prato→Refeição/Sobremesa), múltiplas etiquetas por vídeo e filtro
de pai incluindo descendentes. Etiquetas atuais são planas, categorias já hierárquicas.
Próximo desenvolvimento se autorizado: hierarquia de etiquetas preservando IDs
e associações existentes. Não apresentar esta proposta como funcionalidade entregue.


## Coleções v3 — gestão web; consulta MAG/TV; favoritos em todas (2026-11-03)

Fase anterior committed/pushed d767996. Utilizador esclareceu: gestão sóweb;
MAG/TV consulta, mas favoritos escolhidos/retirados em todas. Implementado:
oculta importar/guardar/editor/opções dos vídeos nas TVs; categorias/listas
abrem seletores de consulta, sem criar/editar/eliminar; pesquisa/filtros/teclado
e progressos mantidos. API recusa gestão de clientes tv/mag e de chaveSamsung,
permitindo favorite/progress. Web inclui Gerir etiquetas com criar/renomear/delete,
normalização de nomes, IDs/associações preservados e confirmação antes de eliminar.

12 testes módulo PASS, incluindo shared rename/no data loss/readonly request guard.
Chrome sem streams: criação/atribuição/renomeação/eliminação de tag e limparfiltro,
modo web por pathname semquery, consulta TV/MAG e favoritos com foco PASS.
Módulov3; TVr21/Samsung1.0.21; web24/MAGr29; APK1.4 igual (hosted UI), instalação
Xiaomi continua pendente por desligada. Atualizar docs/versões Gateway no fecho.

Nova discussão: alinhar tags e categorias. Resposta: categorias=temas amplos;
tags=características combináveis; evitar duplicar Workout como categoria e tag.
Grupos/subníveis poderiam organizar tags (Zona muscular→Pernas→Glúteos) e filtro
da categoria mostrar tags relevantes. Acordado continuar apenas separação web/TV
enquanto se define organização. NÃO implementada hierarquia de tags nem
reclassificação automática nem restrição de tags por categoria. Guardar isto como
proposta em análise, não como funcionalidade entregue. Favoritos são exceção explícita
à consulta nas TVs. Nenhuma alteração aos favoritos IPTV ou à biblioteca Pessoal.


Ativação v3 concluída: backend reiniciado após guarda idle; cliente web/MAG hospedado
recebe módulo3 ao recarregar. Samsung1.0.21 instalada exit0. Durante instalação
final havia playback device=Navegador (verificado no status), por isso apenas o
pacote Samsung foi instalado; não se reiniciou o serviço nem interrompeu o leitor.
Primeira tentativa conservadora recusou instalação por qualquer playback ativo;
identificou-se explicitamente Navegador antes de prosseguir. Testes desta segunda
fase sem transmissões. Xiaomi continua desligada; não instalada APK1.4.


## Títulos dos cartões mais pequenos — Coleções v4 (2026-11-03)

Pedido com screenshot: reduzir títulos dos vídeos. CSS partilhado: web/mobile
15/14→13px, MAG15→14px, TV17→15px; line-height1.35, padding8x10 e min-height50.
Mantém negrito; sem novas regras de truncamento. CSS?v4 e módulo v4; TVr22,
Samsung1.0.22 construída/instalada exit0. Web24/MAGr29 e APK1.4 pendente iguais.
Chrome isolado mudo, leitura apenas: estilos computados13/14/15px e sem overflow
horizontal a390/1280/1536/1920; screenshot desktop inspecionada. Não criar testes
unitários para CSS. Sem vídeos iniciados, sem restart de backend. Instalação
Samsung com guarda para playback Samsung; reprodução no navegador preservada.
Commit/push desta fase. Próximo Ctrl+F5/reabrir Coleções. Categorias/tags continuam
em discussão, hierarquia de tags não implementada; gestão web/favoritos todos mantidos.


## Facebook — capa pública e vídeo sem corte, Coleções v5 (2026-11-03)

Pedido: cartão Facebook sem imagem e reprodução ampliada/cortada. No Chrome,
vídeo natural 720×1280 desenhado 1352×2404 num iframe 1352×650. oEmbed público
devolveu HTML/width, sem título/capa. A página pública forneceu Open Graph e poster
1206×2144. facebook_metadata.py usa apenas hosts HTTPS permitidos, redirects
limitados/validados, sem cookies/autenticação, limites de tamanho e decode Pillow.
Capa PNG até 640px guardada como BLOB na mesma SQLite privada; URL local com digest.
Migração aspect_ratio preserva itens/favoritos/tags/progresso. Metadados em fundo
recuperam capas anteriores sem alterar títulos manuais. Imagens para TV sem chave
em URL, protegidas por LAN/Host; API da biblioteca mantém as proteções existentes.

Leitor oficial FB centrado e escalado para caber inteiro. Resize só altera CSS;
Enquadramento Auto/Vertical/Horizontal/Quadrado corrige posters que não correspondam
ao vídeo. PiP vertical ajustado; títulos pequenos mantidos. Controlos próprios do
Facebook, seguinte manual e sem progresso confirmado por API. Destacar/repor pode
reiniciar iframe, como antes. Não extrai transmissões nem usa o fornecedor IPTV.

Backend ativado após confirmar media/personal/scan/refresh inativos. Produção confirmou
capa PNG local, ratio 0.5625 e título do FB existente. Samsung1.0.23 construída e
instalada exit0; TVr23/Coleçõesv5, web24/MAGr29. Xiaomi desligada: APK1.4 construído,
não instalado; não tentar instalar enquanto desligada.

Validação: 7 testes metadata + 13 Coleções PASS. Bateria101: 100 PASS e um erro
intermitente em test_personal_pipeline; repetição isolada também falhou no encode,
baseline HEAD passou e última repetição no código atual passou (47.4s). Nenhuma
alteração no pipeline Pessoal nem no respetivo teste. Não declarar 101/101 numa
execução. Regressões MAG navigation/TV API/player PASS. Chrome real sem som: capa
360×640, vídeo 720×1280 inteiro e tempo a avançar; resize 1400→390 sem reload;
enquadramento manual/fullscreen/PiP/repor PASS, screenshots inspecionadas. Leitor
de teste fechado. Sem streams IPTV. Facebook em TVs/MAG físicas ainda não validado.

Próximo: Ctrl+F5/reabrir Coleções e confirmar Facebook nas TVs quando conveniente.
Hierarquia tags/categorias continua só proposta; gestão web/favoritos todos mantidos.
Commit/push desta fase e Gateway notes no fecho. Sem novo bloqueio de entrega.


## Origens com seleção múltipla — web25 / MAGr30 / TVr24 (2026-11-03)

O filtro de canais permite marcar várias origens. API aceita origin=MEO,VO como
união antes de aplicar qualidade/deduplicação. Parâmetro simples continua válido;
lista vazia significa todas. Normalização/canonicalização evita resultados distintos
por ordem, repetição ou espaços. Categoria permanece selecionada ao mudar origens.

Web e TVs partilham public/tv/origin-filter.js/css: menu compacto com marcas,
resumo da seleção, aplicação imediata, Todas e Concluir. Teclado e comando:
setas navegam, OK marca/desmarca, Voltar/Escape fecha e devolve foco. MAG usa o
seletor nativo do portal com marcas, múltiplos OK e BACK para concluir. Desmarcar
a última origem volta a Todas. Não modifica favoritos, listas ou progressos.

Validação: 19 testes catálogo e 16 portal PASS; união, qualidade Auto/HD, favoritos,
cache, filtro inválido e categoria cobertos. Regressões MAG e TV API/player PASS.
Chrome sintético sem streams: seleção MEO+VO, remover uma/todas, categoria intacta,
teclado/comando simulado, foco e layouts desktop/mobile PASS; screenshots vistas.
Fixture reproduzível tests/origins_fixture.py e tests/origin-filter-browser.cjs.
Não foram necessários testes de reprodução nem testes do pipeline Pessoal.

Backend ativado com guarda media/personal/scan/refresh inativos; Samsung1.0.24
construída e instalação registada no fecho da fase. Xiaomi continua desligada,
APK1.4 pendente: sem tentativa de instalação. Coleçõesv5 e Pessoalv6 inalterados.
Próximo Ctrl+F5 na web, reabrir app TV ou Restart portal na MAG. Validar o comando
físico quando conveniente. Commit/push e notas Gateway no fecho.


## Preferências de navegação persistentes — 03/11/2026

Pedido: manter escolhas/filtros entre sessões sempre que possível. Implementação
comum ES5 public/tv/browse-prefs.js, armazenamento local por interface/dispositivo
e origem HTTP (endereço/porta). Catálogo web26/MAGr31/TVr25: última secção/tipo,
país, origens múltiplas, categoria, género, qualidade, PT/BR, pesquisa e pasta de
favoritos. Memória independente por secção/tipo; mudar Filmes→TV recupera os filtros
da TV. Portugal é o valor inicial sem preferências. O tamanho/tipo cartões/lista
web já tinha persistência própria e mantém-se. Reabre na primeira página e não
retoma reprodução nem guarda a pilha interna de temporadas/episódios.

Coleçõesv6 guarda categoria, etiqueta, plataforma, lista, favoritos/continuar e
pesquisa. Pessoalv7 guarda vista, tipo, ano, pasta, álbum e pesquisa por vista.
Referências removidas em Coleções/Pessoal e pastas de favoritos desaparecidas
recuperam sem bloquear a interface. Texto de pesquisa guardado imediatamente;
resposta de um filtro anterior já não apaga texto escrito durante a espera.

Preferências localStorage com schema1, campos permitidos e validação simples;
JSON inválido ou storage indisponível não bloqueia a app. Sem campos de tokens,
URLs de reprodução ou leases. Limpeza dos dados do navegador remove preferências;
outro navegador/endereço/dispositivo tem preferências próprias. Favoritos e
progresso continuam partilhados no servidor. MAG depende do armazenamento do WebKit.

Testes PASS: helper (defaults, corrupção, storage bloqueado, campos/valores), MAG
novo portal com as mesmas preferências e troca de secção; regressões MAG/TV;
Chrome web/TV reload e troca de secção; Coleções/Pessoal e recuperação de referências
removidas; fecho completo/reabertura do Chrome com o mesmo perfil restaurou
MEO+VO/Desporto/HD/SPORT sem autoplay. 16 testes portal + 13 Coleções passaram.
Não foram iniciadas transmissões. Fixtures isoladas; dados reais não alterados.

Serviço reiniciado com guarda idle. control.start excedeu a espera enquanto o
processo construía a biblioteca; não foi iniciado outro processo nem terminado o
existente. O processo acabou por ficar pronto; identidade e HTTP confirmados.
Samsung1.0.25 construída/instalada exit0. Xiaomi continua desligada; APK1.4 de
Coleções pendente como antes. Validação física de persistência nas TVs/MAG pendente.
Próximo: atualizar web/reabrir TV/Restart portal; escolhas feitas desde esta versão
ficam guardadas. Commit/push e notas Gateway no fecho. Sem novo bloqueio.


## Destaque com navegação livre — web27 / Coleções7 / Pessoal8 (2026-11-03)

Pedido: destacar, continuar a consultar a interface e substituir o conteúdo ao
escolher outro canal/filme/vídeo; incluir Coleções e Pessoal. Implementado helper
comum ES5 public/tv/floating-player.js para os três leitores web. Chrome/Windows
usa Document PiP e mantém a mesma janela ao mudar de conteúdo ou biblioteca. O
modal/overlay fecha enquanto destacado; barra discreta Repor/Parar e título ficam
na biblioteca. Repor volta ao leitor e à biblioteca que o contém; Parar liberta-o.

Navegação entre TV/filmes/séries, Coleções e Pessoal mantém documentos residentes
em iframes locais, sem descarregar o controlador que ainda reproduz. Só os três
endpoints web da biblioteca admitem framing SAMEORIGIN + frame-ancestors self;
restante portal mantém DENY. O contexto de destaque pode mostrar os media externos
já aceites por Coleções; shell externa de embeds continua isolada sem tokens/dados.
Bridge oficial confirma a janela controladora do módulo, mesmo após mover iframe
para PiP. Um coordenador serializa a transferência e espera a paragem do leitor
anterior. IPTV mantém a proteção de ligação única existente. Fotografias Pessoal
também destacáveis em Document PiP; leitores nativos das TVs/MAG ficam integrais.

Com suporte apenas a PiP nativo, usa-se a capacidade do navegador; a continuidade
de janela ao trocar de biblioteca depende desse suporte. Document PiP requer
contexto seguro (loopback ou HTTPS configurado) e navegador compatível. Mover
embeds oficiais pode recarregar o iframe; YouTube retoma a posição conhecida.
Facebook continua com controlos próprios e seguinte manual. Fechar/navegar para
fora de toda a app termina o contexto; não há cache de transmissões.

Testes Chrome isolado/mudo PASS: vídeo sintético IPTV progride enquanto se navega;
trocar filme→canal mantém a janela e envia stop antes de novo start; abrir Coleções
preserva o leitor até escolher MP4 público; seleção liberta lease IPTV; YouTube
real mudo na janela partilhada; Pessoal vídeo continua ao consultar fotos, escolher
foto substitui vídeo e liberta lease pessoal; identidade da mesma janela confirmada;
Repor/Parar terminam corretamente. Screenshot da biblioteca livre inspecionada.
Uma execução com build SDK concorrente não confirmou vídeo Pessoal a tempo; bateria
de integração repetida sem builds passou completa. Testes anteriores falharam por
espera da transição e asserção currentSrc; agora verificam estado/source/pausa.
13 Coleções + 16 portal e regressões MAG/TV passaram. Testes sem fornecedor real.

Samsung pacote1.0.26/TVr26 preparado (alterações de destaque destinam-se à web);
MAGr31 mantém-se, Coleções7/Pessoal8 partilhados. Xiaomi continua desligada,
APK1.4 pendente. Ativação backend requer reinício para novas rotas estáticas/CSP.
Neste ponto havia reprodução Navegador ativa; solicitada confirmação de leitor
fechado. Não reiniciar/interromper enquanto essa confirmação estiver pendente.
Próximo: ativar após confirmação, Ctrl+F5, escolher Destacar e navegar normalmente.
Commit/push desta fase e Gateway notes no fecho.


Fecho desta fase: utilizador confirmou «Já fechei; podes ativar». Backend reiniciado
com guarda idle e identidade confirmada; web/aliases de floating-player.js deram200,
as três páginas web têm SAMEORIGIN/self e index MAG mantém DENY. Samsung1.0.26
instalada. Estado atual ATIVO, não continuar a reportar confirmação pendente.

Validação adicional PASS: fallback PiP nativo (catálogo livre, entrar/sair, pausa,
sem nova ligação ao destacar); Coleções Document PiP com YouTube real mudo,
pausa/retoma, reposição, posição preservada, destacar em pausa e fechar pelo X;
MP4 destacado sem trocar source. Detetado e corrigido estado «A reproduzir» antigo
enquanto iframe recarregava: agora mostra «A retomar…» e só habilita pausa após
ready. Bridge autoriza nonce/origem e módulo proprietário ou seu proxy PiP.
Regressão de navegação Pessoal web/MAG/TV/mobile passou, incluindo foco e álbuns.
Screenshot da biblioteca livre com barra Em destaque inspecionada. Sem fornecedor
real nem stream deixado ativo pelos testes. Commit/push no fecho; Ctrl+F5 para
carregar web27. Testes antigos PiP alinhados ao novo modo e fallback nativo.


## Pessoal compacto — v9 / TVr27 (2026-11-03)

Pedido com screenshot: cartões demasiado largos e poucos itens por página.
Grelha responsiva: web mínimo170px, 12 colunas a2466px, cartões ~183px versus4
colunas anteriores; thumbnails86px, títulos13px em duas linhas, pasta12px e ações
compactas. Fallback float em6colunas para MAG sem Grid; TV/MAG títulos14px, TV
mínimo200px na grelha moderna; mobile2colunas. Tooltips mantêm nome/pasta completos.

Default web60 por página (antes12), TV30, MAG24. Seletor12/24/30/60 no rodapé,
guardado por vista nas preferências existentes. API já aceita até60: sem alterações
no backend nem reinício. Imagens carregam lazy nos navegadores compatíveis.
Galeria de fotos conserva filtro/tamanho próprios, para mudar quantidade na
biblioteca durante destaque sem duplicar/saltar fotos ao atravessar página.

Chrome sintético com135 itens, sem streams: 60/60/15, página anterior/seguinte,
troca para24/reload persistente, grelha desktop/mobile sem overflow, TV30/MAG24
e comando CH+/- PASS. Galeria manteve sequência foto060 após mudar biblioteca
de60 para24. Screenshots inspecionadas com miniaturas carregadas.8 testes Pessoal
PASS. Testes de reprodução existentes escolhem12 explicitamente; navegação aceita
os novos defaults. Não houve reprodução nem chamadas ao OneDrive real/fornecedor.

Pessoalv9, web27/MAGr31/Coleções7 mantidos; Samsung1.0.27/TVr27 construída.
Mudança ativa nos ficheiros servidos, sem interromper leitores. Instalação Samsung
e commit/push registados no fecho. Xiaomi desligada/APK1.4 pendente como antes.
Próximo Ctrl+F5/reabrir Pessoal e escolher a quantidade no rodapé. Sem bloqueio novo.


## Menu Pessoal redesenhado — v10 / TVr28 (2026-11-03)

Pedido: menu feio, elementos amontoados; melhorar apresentação e ícones. Agora
tem barra lateral com seis secções e ícones SVG inline consistentes; seleção teal
com rebordo e indicador lateral; cabeçalho Pessoal/Media Forge Lab com versão10.
Pesquisa com lupa/teclado e filtros Ano/Pasta alinhados num painel, Novo álbum
visível. OneDrive tem cartão de ligação; Gerir biblioteca expande painel de gestão
com pastas/atualização/desligar e estado detalhado, evitando ações amontoadas.
Cabeçalho da grelha junta título, contagem e Opções do item; removida a folga do
status vazio. Cartões compactos/quantidade persistente da fase anterior mantidos.

Mobile: secções3×2 com ícones, conta compacta e filtros adaptáveis. SVG decorativo
aria-hidden, botões só com ícone têm nome acessível, secção aria-pressed e painel
aria-expanded. Setas → saem da barra lateral para a grelha; ← na primeira coluna
regressa à secção; BACK fecha gestão. Layout tem fallback float/WebKit prefixado.

Chrome metadata-only135 itens PASS: web1887px/mobile390px/TV1920/MAG1280 sem
overlap/overflow; ícones, seleção, abrir/fechar gestão, setas e Opções do item.
Screenshots desktop/mobile/gestão inspecionadas. Regressão compacta60/60/15,
quantidade persistente, sequência fotos e paginação por comando passou. Sem
reprodução, ações OneDrive reais, alteração de dados ou reinício do servidor.
Pessoalv10 ativo nos ficheiros servidos. TVr28/Samsung1.0.28 reconstruída/instalada
no fecho. Web27/MAGr31/Coleções7 mantidos; Xiaomi desligada/APK1.4 pendente.
Próximo Ctrl+F5/reabrir Pessoal e confirmar v10; testar apresentação física quando
conveniente. Commit/push e Gateway notes no fecho. Sem bloqueio novo.


## Títulos Coleções mais pequenos — v8 / TVr29 (2026-11-03)

Utilizador continua a achar os títulos demasiado grandes. Ajustado explicitamente
para12px web/mobile,13px MAG e14px TV, peso600 (evita bolder herdado do botão),
apenas2linhas e reticências. Altura de texto32/36/38px, margens exteriores para não
deixar a3.ªlinha aparecer no padding do line-clamp. Metadados12px/TV13px. Nome
completo preservado no DOM e title do botão, sem alterar os nomes guardados.
Coleçõesv8/CSSv8/JSv8; TVr29/Samsung1.0.29 reconstruída/instalada no fecho;
web27/MAGr31/Pessoal10 mantidos. Não houve reinício nem reprodução.

Verificação visual Chrome com títulos sintéticos longos: web1920/mobile390,
TV1920/MAG1280 com fonte/peso/altura corretos, limite2linhas, tooltip completo e
sem overflow. Screenshot inspecionada após corrigir bleed do padding. Sem novos
testes unitários para CSS. Próximo Ctrl+F5 em Coleções, confirmarv8. Commit/push
e notas Gateway no fecho; sem bloqueio novo.


## Categoria automática Por classificar — Coleçõesv9 / TVr30 (2026-11-03)

Pedido: categoria predefinida que exista sempre para vídeos não classificados.
Categoria virtual id=uncategorized, nome Por classificar, system=true; devolvida
em primeiro lugar pela API, mesmo vazia. SQL NOT EXISTS item_categories reúne
vídeos sem categorias reais; etiquetas não contam como categoria. Atribuir uma
categoria retira-o automaticamente; remover a última ou eliminar a categoria
devolve-o. Sem migração, associações artificiais, cópias ou alteração de favoritos,
tags, listas e progresso. Contagem global própria. Filtro combina com favoritos,
pesquisa, plataforma e listas existentes; API category=uncategorized.

API impede editar/eliminar esta categoria e usá-la como mãe. UI gestão mostra-a
como Automática, sem ações de edição; editores excluem-na dos pais/checkboxes.
Sem categorias marcadas guarda Por classificar implicitamente; importação com
este destino também é suportada. Preferência de filtro continua persistente.

15 testes Coleções +7 metadadosFacebook PASS: presença vazia/permanente, inclusão
automática, transições, filtros, proteção, importação, reabrirDB e dados preservados.
Chrome sintético web/TV/MAG PASS: opção sempre visível, reload, classificar sai da
lista, editor/gestão protegidos e eliminar última categoria devolve vídeos. Sem
reproduções/fornecedor/OneDrive real. Pacote Samsung1.0.30/TVr30 preparado.

Ativação exige reiniciar backend. Guarda inicial adiou porque começou reprodução
Navegador após a leitura idle. Solicitada confirmação de fechar o leitor; não
reiniciar até essa confirmação. Coleçõesv9, web27/MAGr31/Pessoal10 mantidos.
Próximo ativar após confirmação e Ctrl+F5; instalação/commit/push/Gateway no fecho.


## Correção Coleções na MAG — v10 (2026-11-03)

Pedido: Coleções não funciona na MAG e deixa o utilizador sem conseguir sair.
Reprodução controlada com capacidades antigas simuladas: sem evento XHR2 onload,
a versão anterior ficava com zero cartões; sem button.click, BACK lançava TypeError.
Não se obteve um diagnóstico da MAG física; esta evidência demonstra os caminhos
de incompatibilidade, não identifica com certeza o firmware/capacidade da box.

Pedidos usam agora readyState + prazo manual, conclusão única e recuperação 403
limitada. Shell MAG autónoma instalada antes de preferências/opcionais: erro de
arranque não remove saída, BACK/ESC regressam ao portal e MENU sai diretamente.
Navegação via document.onkeydown, keyCode/which/window.event e returnValue; OK
invoca a ação sem button.click. BACK funciona também no campo de pesquisa; edição
de combo/teclado fecha antes. Desliga spatial navigation nativa conforme Infomir.
Voltar fecha primeiro teclado/dialog/leitor, depois portal; link Biblioteca tem href.
Falha do HTML5 video não impede Stop da API nativa. Iframe externo não fica com
o foco do comando: controlos da biblioteca retomam o foco na MAG. InitPlayer usa
SetTopWin(0); formatos/players sociais continuam oficiais, sem extração indevida.

CSS MAG explicita top/right/bottom/left e layouts simples onde inset/grid/flex
deixavam menus/leitor fora do ecrã. Foco destacado e ajuda Voltar/MENU visível.
Títulos compactos preservados. Sem alterações aos catálogos, favoritos ou streams.

Validação: tests/collections-mag-http.cjs PASS (readyState, erro, JSON inválido/null,
timeout, eventos repetidos e retry403). tests/collections-mag-browser.cjs PASS com
fixture tests/collections_mag_fixture.py: lista, favoritos, setas/OK/BACK/MENU,
pesquisa/combo, overlays com inset removido antes de interpretar CSS, native mock,
Stop apesar de erro HTML5, foco iframe, helper ausente, API recusada e erro de ação;
smoke web/TV. Acorn ES5 dos quatro scripts partilhados PASS. navigation.cjs PASS;
22 testes Python Coleções/metadados PASS. Sem reprodução externa/fornecedor real.

Coleções v10 (JS/CSS10) já servida em HTTP; bytes ativos conferidos com o repo.
Não foi preciso reiniciar backend e reprodução Navegador ativa foi preservada.
MAG principal continua r31/web27/TVr30/Pessoal10. Samsung instalada continua1.0.30
com Coleçõesv9 empacotadas; esta correção MAG não precisa reinstalar apps TV.
Categoria Por classificar do checkpoint anterior continua com ativação backend
pendente: ainda sem confirmação de fecho do leitor. Não reiniciar com stream ativo.

Próximo: utilizador faz Restart portal e valida Coleçõesv10 na MAG (lista/Voltar
e reprodução social física). Foi pedida confirmação assíncrona. YouTube/Facebook
no navegador antigo continuam dependentes da capacidade real da MAG; teste feito
no PC apenas simula limites e não confirma imagem/som na box.


## Coleções TV: capas completas e opções — v12 / Samsung1.0.31 (2026-11-03)

Pedido: na TV as capas ficam recortadas e as opções de vídeo são difíceis de
navegar, feias e mal formatadas. Correção partilhada: imagens dimensionadas pela
proporção original, max-width/max-height e centragem com transform WebKit, sem
depender de object-fit. Testadas capas horizontais, verticais e quadradas.
TV: painel lateral dedicado às opções do leitor, SVGs discretos, botões espaçados,
fila/vídeos anterior-seguinte, retomar/pausa, posição e ecrã inteiro; foco destacado.
Overlays com top/right/bottom/left explícitos; fallback grid-gap e margens onde o
Tizen2019 não suporta inset/flex-gap. Botão Coleções alinhado e painel sem sobrepor
vídeo. Ecrã inteiro TV/MAG mantém o comando no documento: OK/setas mostram opções,
Voltar regressa às opções antes de fechar o vídeo. Links Abrir na origem ocultos
nas TVs/MAG pois aí não permitem abrir a app de origem.

Cartões TV/MAG têm Opções com ações de consulta Reproduzir/Favorito, SVGs e título
completo. Sem gestão/importação/edição de categorias nas TVs/MAG. Voltar repõe foco
no cartão; seleções e favoritos persistentes. Iframe externo deixa o comando no
painel nas TVs também; não altera suporte de reprodução/autorização das origens.

MAG física: utilizador confirmou v11 sem cartões E sem saída. Não considerar a
correção v10 validada. Encontrada sintaxe não portátil ES5 strict: FunctionDeclaration
dentro de else (play/attach). Acorn antigo do SDK aceitava-a mesmo ecmaVersion5;
novo teste AST rejeita esse caso explicitamente. Convertidas em expressões de
função. Shell de saída movida para player.js carregado antes de collections.js;
scoped apenas ao DOM Coleções para não interferir com Pessoal/TV. Se o ficheiro
principal nem sequer carregar/interpretar, Voltar/MENU continuam disponíveis e
surge mensagem após 8s. Hipótese forte para os sintomas, sem diagnóstico direto
do parser físico. Nova confirmação MAGv12 pedida, ainda pendente.

Validação: collections-tv-browser.cjs PASS em720p/1080p sem inset/gap, capas3rácios,
menus de consulta/foco, todas8opções leitor por setas reais, nativeAVPlay mock e
ecrã inteiro/Voltar, sem streams reais. Regressões MAG/componente HTTP/ES5/TVPlayer/
navegação principal PASS; gestão de etiquetas web e só consulta TV/MAG PASS.
Na Samsung física: app1.0.31/Coleçõesv12 instalada, lista aberta, Opções→Reproduzir/
Favorito por MagTV.remote com sucesso, Voltar repõe cartão;7capas carregadas e7
com proporção/limites corretos. Nenhum vídeo aberto nem stream fornecedor iniciado.
Leitor real/imagem/som não retestados nesta fase; opções leitor verificadas no PC.

Sem restart backend; leitor Navegador preservado. FrontendHTTP Coleçõesv12; TVr31,
MAGprincipalr31/web27/Pessoal10. Samsung1.0.31 instalada. Xiaomi continua desligada,
instalação das alterações pendente. Categoria Por classificar continua pendente de
restart seguro após confirmação de fecho do leitor; sem resposta a essa pergunta.
Próximo: confirmar MAGv12 e validar aspeto/comando no leitor da TV com utilizador.


Fecho desta fase: Samsung1.0.31 reinstalada com os ficheiros finais e app lançada
normalmente (debug0), sem abrir conteúdos. AndroidTV APK1.5/code6 compilado e
assinado, com Coleçõesv12; adb devices vazio, pelo que Xiaomi não foi instalada.
Browser do utilizador continuou ativo e backend não foi reiniciado. Confirmação
MAGv12 ainda não recebida; não confundir testes de simulação com validação física.


## Confirmação física MAG Coleçõesv12 — 2026-11-03

Confirmação física do utilizador em 03/11/2026: na MAG com Coleções v12 aparecem os cartões e consegue sair. Carregamento/lista e saída validados na box; retirar pendência desses dois pontos. Reprodução social/imagem/som na MAG ainda não confirmados. Sem alterações de código, restart ou streams neste checkpoint. Mantêm-se instalação Xiaomi pendente (APK1.5 preparado) e ativação backend Por classificar dependente de fecho confirmado do leitor; esta resposta não autoriza restart.
