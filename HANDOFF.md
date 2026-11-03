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
