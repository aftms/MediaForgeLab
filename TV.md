# Media Forge Lab para televisões

O portal MAG e a aplicação web continuam a usar o mesmo serviço. A interface TV
está em `public/tv/`, em JavaScript ES5, com páginas de 30 títulos e navegação pelo
comando. O computador precisa de permanecer ligado.

## Aplicações

- **Samsung:** aplicação Tizen 5.0, identificador `MAGForge01.MagForgeLab`.
  Instalada na Samsung QE55Q67RATXXC (2019). Usa Samsung AVPlay.
- **Xiaomi / Android TV:** APK `local.magforgelab.tv`, Android 8 ou superior.
  Inclui ícone e banner na lista de aplicações TV. Usa o leitor nativo Android
  (VideoView/MediaPlayer), com a interface do portal num WebView restrito ao
  endereço local configurado. Modelo confirmado pelo dispositivo: MiTV-MOOQ1, Android 10; não assumir A2.

Catálogos completos, pesquisa, países, categorias e filtro opcional PT/BR;
favoritos separados por tipo, pastas existentes, continuar a ver, temporadas e
episódios. Criar/reordenar pastas continua disponível na aplicação web.
A atualização usa o mesmo catálogo e o mesmo estado de execução das outras UIs.

## Comando

- No menu esquerdo, **→** entra diretamente nos conteúdos.
- Setas percorrem títulos e botões; **OK** escolhe ou reproduz. A pesquisa com
  lupa fica no canto superior direito, sem duplicação na coluna esquerda.
- **↑** permite chegar à pesquisa/filtros. Nos seletores, OK abre as opções;
  depois de escolher, **↓** passa aos conteúdos. Na pesquisa, ↓ também sai para
  os conteúdos. **Voltar** regressa à temporada, série ou menu.
- CH+/CH− mudam de página. A estrela ao lado do título guarda/remove favorito.
- Durante a reprodução, Voltar fecha o leitor; as setas mostram os controlos.
- Pausa liberta a ligação. Retomar prepara novamente o vídeo na posição guardada.
- Avançar/retroceder usa passos de 30 segundos, com um pedido de cada vez.
  Idioma do áudio e modo compatível estão no leitor. Conversão de legendas
  embutidas ainda não está incluída nesta primeira versão TV.

## Ligação única e privacidade

Os leitores TV usam `/api/media/web` com o mesmo bloqueio global da MAG/web.
Só o servidor contacta o fornecedor. Entrega HLS local: remux quando possível,
transcodificação quando necessária. Nos canais das TVs, prepara o vídeo numa
única ligação, sem uma análise preliminar separada: conserva o vídeo original,
preserva áudio na Samsung e normaliza áudio AAC na Android TV. O modo Compatibilidade
faz análise completa e transcodificação, incluindo os formatos que a TV recusar. Não existem transmissões no cache offline.
Aplicações externas que se liguem diretamente ao fornecedor não são controladas
por este bloqueio.

Samsung: o pacote privado inclui uma chave **local do portal**, nunca os dados
do fornecedor. A chave está em `.runtime/tv-access.json`. Só uma lista limitada de
endpoints aceita acesso de aplicações instaladas; pedidos reais exigem essa chave,
as alterações exigem também o token de ação, e mantêm-se os limites LAN e Host.
Preflight CORS não concede acesso aos dados. Não existe `Access-Control-Allow-Origin: *`.
Não há acesso TV a `/api/source`, controlo do processo ou ficheiros privados.

Android: navegação, recursos e reprodução são limitados à origem LAN compilada;
sem acesso a ficheiros locais, sem permissões de armazenamento e sem permissões
para instalar outras apps. HTTP é permitido apenas para o endereço privado do PC
no manifesto de segurança. Não há aceitação de certificados inválidos. Esta
instalação privada LAN não requer configurar a CA da PWA na TV.

## Compilar e instalar novamente

1. `preparar-apps-tv.bat`: cria os dois pacotes com os SDKs existentes.
2. `instalar-samsung.bat` ou `instalar-xiaomi.bat`: instala o pacote correspondente.
   Não abre a aplicação automaticamente nem altera a HealthForgeLab.
3. Abra **Media Forge Lab** na lista de aplicações da TV.

Destinos locais: `.runtime/tv-devices.json` (não publicado). Para outro IP:
`py -3 install_tv.py samsung --ip 192.168.1.229` ou
`py -3 install_tv.py android --ip 192.168.1.90`.

Pacotes: `.runtime/tv-build/MediaForgeLab-Samsung.wgt` e
`.runtime/tv-build/MediaForgeLab-AndroidTV.apk`. O WGT contém a chave local: manter
privado. Todos os pacotes, chaves e certificados ficam fora de Git.
Não apagar a chave Android `.runtime/tv-android-signing.p12` se pretender atualizar
o APK sem desinstalar. A password fica num ficheiro privado adjacente.

Samsung requer Developer Mode e o perfil de assinatura existente
`HealhForgeLabTV`; para outro perfil use `build_tv.py --target samsung --profile NOME`.
O build não exporta nem altera certificados do Tizen. Android usa os build tools
35.0.1, plataforma 35 e JDK do Android Studio já instalados, sem Gradle/downloads.
Depuração e autorização do computador na Xiaomi são feitas pelo utilizador.

## Validação em 03/11/2026

- Pacotes WGT e APK compilados e assinados; APK verificado com apksigner.
- 61 testes Python de catálogo, atualizações, preservação, HTTP, CORS TV, ligação
  única e FFmpeg sintético; testes de regressão do comando MAG e sintaxe ES5 TV.
- Chrome isolado com catálogo sintético: comando, pesquisa enquanto escreve,
  filtros, paginação, favoritos por tipo, temporadas/episódios, avanço, pausa,
  retoma e saída. Leitores nativos simulados neste teste; nenhum acesso ao fornecedor.
- Samsung física: instalação e abertura confirmadas via SDB; Tizen 5.0 e AVPlay
  presentes. Catálogo carregado; navegação corrigida e confirmada pelo utilizador.
  Viewport 1280×720, controlos e lista dentro do ecrã.
- RTP 1 físico: AVPlay em PLAYING com relógio a avançar até 37,8 s. Outro dispositivo
  recebeu HTTP 409 durante a reprodução. Voltar libertou a ligação. Imagem e som confirmados pelo utilizador. Filmes/episódios ainda precisam de
  teste físico; avanço/pausa/retoma passaram no teste sintético.
- Xiaomi: instalada na MiTV-MOOQ1, Android 10, com ADB autorizado pelo utilizador.
  Ecrã real de 1920×1080 capturado e revisto. RTP 1 reproduzido pelo MediaPlayer nativo; relógio a avançar, HLS recebido e
  Voltar libertou a ligação. Arranque medido em 15,3 s. A captura ADB da camada de
  vídeo ficou preta; essa captura não comprova imagem, e imagem/som precisam de
  confirmação humana.
- Medição final Samsung: arranque em 14,5 s e AVPlay em PLAYING. A aplicação
  tem de estar em primeiro plano: recarregar apenas a página pelo depurador pode
  perder o foco e deixar o AVPlay em IDLE apesar de receber segmentos. Para testar,
  usar `tizen run` após iniciar o depurador; não confundir esse estado com falha do
  formato. `stop` e `close` são isolados para recuperar de preparação interrompida.
- A aplicação renova automaticamente o token de ação uma vez após HTTP 403,
  evitando «Pedido recusado» depois de reiniciar o servidor.
- «Sair para a TV» fecha a app. A Samsung pode voltar à entrada HDMI da MAG;
  nesse caso o portal visível é o da box, não a aplicação Samsung.
- Os favoritos, organização e progresso existentes foram preservados na ativação.

Referências: [Samsung AVPlay](https://developer.samsung.com/smarttv/develop/api-references/samsung-product-api-references/avplay-api.html),
[Tizen CLI](https://developer.samsung.com/smarttv/develop/getting-started/using-sdk/command-line-interface.html),
[Android TV](https://developer.android.com/training/tv/get-started/create),
[segurança WebView](https://developer.android.com/privacy-and-security/risks/insecure-webview-native-bridges).

## Identidade Media Forge Lab (r7)

Nome e símbolo atualizados em MAG, web/PWA, gestão e lançadores TV. Os IDs
técnicos Tizen/Android, certificado HTTPS, chaves de armazenamento e assinatura
são mantidos para atualizar a instalação existente e preservar os dados.

## País inicial dos canais

A secção TV abre em Portugal (PT). Pode escolher outro país; na MAG, use
BACK ou MENU → Países e categorias. Filmes, séries e favoritos mantêm os
seus filtros habituais. Ao voltar à secção TV, Portugal é novamente o padrão.

## Arranque Android TV — APK 1.2 (03/11/2026)

O proxy encaminha os bytes disponíveis sem esperar por blocos de 64 KiB.
Nos canais Android, análise inicial limitada a 1 s/1,5 MB e segmentos HLS
com alvo de 2 s, sempre alinhados com keyframes. O vídeo continua copiado;
áudio AAC, ligação única e limpeza ao parar mantêm-se. Samsung, filmes,
episódios e modo Compatibilidade conservam os parâmetros anteriores.
O tempo real de cada segmento depende dos keyframes que o fornecedor envia.
Se uma emissão tiver faixas que só aparecem mais tarde, usar Compatibilidade,
que mantém a análise completa. Não existe promessa de arranque instantâneo.

A app mantém o ecrã acordado já durante a preparação, assinala URLs recusados
e disponibiliza apenas estado/tempos do leitor para diagnóstico. O serviço
expõe tempos de abertura, primeiros bytes e playlist em /api/media/status,
sem URLs ou credenciais. APK final assinado, instalado e aberto na Xiaomi;
depuração WebView desativada na versão instalada.

Medições sequenciais autorizadas na MiTV-MOOQ1, sem outros leitores:

- RTP 1 HD, ID 224, categoria PT| VODAFONE: cerca de 15–16 s até relógio
  nativo >1 s, dos quais ~12 s na preparação. Reduzir buffers não resolveu.
  Um fotograma descodificado do segmento local estava inteiramente preto;
  não era apenas a limitação de captura da camada de vídeo Android.
- RTP 1 HD, ID 500, categoria PT| GENERALISTAS: 4,2–4,8 s até relógio >1 s;
  playlist pronta em ~1,2–1,3 s. O segmento local continha imagem normal
  RTP 1, H.264 1080p. Comparação com os parâmetros anteriores no mesmo canal:
  5,0 s. Amostras pequenas, sujeitas a variações do fornecedor/rede.
- Estes tempos incluem pelo menos 1 s de reprodução; não são medições óticas
  do primeiro fotograma no ecrã da TV. Som/imagem física continuam a exigir
  confirmação humana. Não interpretar 15→4 s como ganho no mesmo stream:
  a diferença principal foi entre duas versões do fornecedor.

A seleção automática de variantes não foi alterada a partir desta amostra.
Para escolher a alternativa: Portugal → categoria PT| GENERALISTAS → HD →
pesquisar RTP 1. Qualidade «Todas» mostra também as variantes repetidas.
Favoritos e organização mantêm-se. Nenhuma transmissão ficou ativa após os testes.

Validação final: 62 testes Python, incluindo proxy com emissor em duas rajadas,
FFmpeg real sobre vídeo sintético, exclusão entre dispositivos, falha de origem,
remux/transcodificação e limpeza; regressões JavaScript MAG/TV passaram.

## Filtro de origem dos canais — web v9 / TV r9 / MAG r21

Web e TVs: seletor «Todas as origens» junto de país/categoria/qualidade.
MAG: Opções → Origem dos canais. Filtra os canais e os favoritos de canais;
filmes e séries não têm este filtro. Entrar novamente na secção TV repõe
Todas as origens. País, categoria, pesquisa e qualidade podem ser combinados.

Classificação comum no servidor: prefixos VO/VODAFONE, MEO, NOS, VIP; quando
falta prefixo usa a identificação explícita nas categorias. PT identifica a
lista geral do fornecedor; os restantes ficam em Origem não indicada. Só são
apresentadas origens existentes no país. Não é uma identificação técnica da
rede do stream. Nenhuma fonte foi apagada, excluída automaticamente ou testada
para reprodução nesta fase. As origens são enumeradas antes da deduplicação;
a seleção por origem também precede Auto, preservando versões alternativas.
Favoritos continuam associados à família do canal.

Validação: 66 testes Python, regressões JS MAG/web/TV e Chrome real sobre o
catálogo local, em 1280×720 e 390px. Verificados MEO/VO/PT, pesquisa combinada,
filtro oculto nos filmes e reposição ao entrar em TV. Hashes de catálogo,
favoritos, organização e progresso iguais antes/depois do reinício.
Samsung 1.0.9 assinada e instalada. Xiaomi usa a UI partilhada r9 ao reabrir,
sem novo APK (continua 1.2). Recarregar a web com Ctrl+F5 e reiniciar portal MAG.

## Filtros VOD — TV r10

Samsung 1.0.10 instalada; Xiaomi usa a mesma UI r10 sem reinstalar APK1.2.
Filmes e séries têm seletores de país/idioma do catálogo e género, combináveis
com categoria e pesquisa. Não filtra pelo país de produção. Metadados incompletos
ficam em Sem género indicado. Reabrir a aplicação para carregar a nova interface.
