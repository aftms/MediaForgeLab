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
