# Media Forge Lab — Windows, Android e gestão local

Versão web 3 / portal MAG r19, 3 de novembro de 2026.

## Endereços nesta casa

| Utilização | Endereço |
|---|---|
| Aplicação web neste Windows | http://127.0.0.1:8091/web/ |
| Android, tablet ou outro computador da LAN | https://192.168.1.240:8443/web/ |
| Gestão neste Windows | http://127.0.0.1:8092/ |
| Portal 1 URL da MAG | http://192.168.1.240:8090/ |
| Certificado público para instalar no Android | http://192.168.1.240:8090/web/ca.cer |

No **Admin → Ecosystem UIs → Media Forge Lab → Abrir**, encontra o painel de gestão:
estado, iniciar, parar, reiniciar e ligações para as interfaces. A aplicação web
é a ligação **Aplicação web · Windows** nesse painel. É aí que os filmes e
episódios reproduzem no navegador; a interface MAG usa o leitor nativo da box.

O catálogo do Admin verifica a disponibilidade do painel. O próprio painel
mostra se o portal está efetivamente ligado. Iniciar/parar/reiniciar são feitos
dentro deste painel, usando a identidade e o token privados da instância.
O gestor genérico do Admin não consegue confirmar o proprietário das portas
neste Windows: a tabela TCP devolveu estado 0/nulo para listeners ativos.
A integração não contorna essa verificação nem termina processos desconhecidos.

## Iniciar e parar

Na pasta `D:\Workspace\MediaForgeLab`:

- **iniciar-portal.bat**: inicia o painel de gestão e o servidor em segundo plano.
- **parar-portal.bat**: termina o portal, incluindo HTTP, HTTPS e qualquer reprodução.
- **estado-portal.bat**: confirma a instância do portal.
- **iniciar-gestao.bat**: disponibiliza só o painel, mesmo com o portal parado.

O painel fica disponível para voltar a iniciar o portal. Depois de reiniciar
o Windows, execute `iniciar-portal.bat`; não foi instalado arranque automático.
O computador deve ficar ligado e sem suspensão durante a utilização.

## Instalar como aplicação

**Windows:** abra o endereço Windows no Chrome/Edge. Use **Instalar aplicação**
ou a opção de instalação na barra/menu do navegador. O endereço loopback é
aceite como contexto seguro para PWA; o HTTPS também está preparado e o
certificado local já foi instalado no utilizador atual deste Windows.

**Android, ligado ao Wi-Fi de casa:**

1. Descarregue `Media Forge Lab-CA.cer` pela ligação do certificado acima.
2. Nas Definições do Android, procure **Instalar certificado**. Normalmente fica
   em Segurança e privacidade → Mais definições de segurança → Encriptação e
   credenciais → Instalar certificado → **Certificado CA**. Escolha o ficheiro
   descarregado e confirme com o PIN do dispositivo. Os nomes variam por fabricante.
3. Abra **https://192.168.1.240:8443/web/** no Chrome. O certificado deve ser
   reconhecido sem erro; ignorar um aviso de certificado não substitui a instalação.
4. Use **Instalar aplicação**, ou menu do Chrome → Adicionar ao ecrã principal
   → Instalar. Abre numa janela própria com o ícone Media Forge Lab.

A CA foi criada localmente para esta instalação. Só o certificado público é
descarregado; a chave privada fica no computador. Orientação oficial sobre os
menus Android: [Google — certificados](https://support.google.com/pixelphone/answer/2844832?hl=pt).
Requisitos da PWA: [MDN — instalação](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Making_PWAs_installable).

## Biblioteca e reprodução

- TV em direto, filmes e séries completas, com temporadas e episódios pedidos
  apenas ao abrir a série. País, categoria, pesquisa e qualidade nos canais.
  PT/BR é opcional. Os cartões usam ilustrações locais; não são capas de filmes.
- Favoritos partilhados, separados em Canais / Filmes / Séries; abrem nos canais.
- Continuar a ver usa o mesmo progresso da MAG e repõe episódios guardados após
  reiniciar. O progresso é guardado periodicamente e ao fechar/pausar o leitor.
- Atualizar catálogo utiliza o mesmo serviço transacional, informa data/resultado
  e mantém o catálogo anterior se houver falha. As exportações permanecem em
  `D:\Workspace\share\IPTV`. Definições permite mudar o URL com o campo oculto.
- O vídeo tem controlos nativos, barra para a posição no filme completo,
  saltos de 30 segundos, seleção de áudio quando há várias faixas e modo compatível.
  Na pausa, liberta a ligação e conserva a posição; ao retomar volta a prepará-la.
  Na TV, retomar volta ao direto. Legendas incorporadas não são convertidas nesta
  primeira versão web; as opções nativas da MAG mantêm-se.
- H.264 de 8 bits é normalmente copiado para HLS, sem recompressão de vídeo.
  Áudio incompatível é convertido para AAC. Outros vídeos são convertidos para
  H.264; o botão Modo compatível também permite essa conversão. A capacidade do PC
  limita a conversão, sobretudo de 4K. A qualidade escolhida em TV seleciona uma
  versão do canal, não melhora a resolução do ficheiro de um filme.
- Nos testes reais, a preparação inicial demorou cerca de 25–30 segundos.
  Mudar a posição ou o áudio pode voltar a preparar a ligação. Isto não é um
  serviço de vídeo pré-descarregado.

## Cartões compactos ou lista

Acima dos conteúdos, escolha **Cartões** ou **Lista**. Os cartões têm uma
ilustração pequena e ocupam aproximadamente metade da altura anterior. A lista
mostra linhas compactas, distribuídas por colunas quando existe espaço, com nome,
categoria, qualidade e favorito. No telemóvel, usa uma coluna.

**Por página** permite escolher **60, 120 ou 240** conteúdos. Por defeito são 60
nos cartões e 120 na lista. O navegador guarda a vista escolhida e a quantidade
por vista, mesmo depois de recarregar. A preferência aplica-se também a filmes,
séries, episódios e favoritos; o servidor continua a entregar só a página pedida.
O limite pequeno usado pela MAG mantém-se: esta alteração é da interface web.

## Pastas e ordem dos favoritos na web

Em **Favoritos**, escolha **Canais**, **Filmes** ou **Séries**; cada tipo tem as
suas pastas. **+ Nova pasta** cria um grupo. O seletor **Pasta** alterna entre
Todos os favoritos, Sem pasta e os grupos criados. Ao selecionar um grupo,
pode renomeá-lo ou apagá-lo. Apagar a pasta move os seus favoritos para Sem pasta,
sem remover estrelas nem conteúdos.

Prima **Organizar**: cada cartão mostra a posição, botões para ir ao início,
subir, descer ou ir ao fim, e um seletor para o mover para outra pasta.
As alterações são guardadas imediatamente no servidor e partilhadas entre
navegadores. Para ordenar, limpe os filtros e deixe a qualidade em Auto; os
filtros continuam disponíveis para procurar e distribuir favoritos pelas pastas.
Conclua com **Concluir organização**. Não é necessário arrastar, pelo que também
funciona com toque no telemóvel.

A ordem e as pastas usam os identificadores estáveis dos favoritos (família do
canal, filme ou série), sobrevivem a reinícios e atualizações do catálogo e ficam
em `.runtime/favorite-layout.json`, com cópia anterior e gravação transacional.
Se dois dispositivos alterarem a organização ao mesmo tempo, uma alteração
desatualizada é recusada e a lista recarrega. As pastas são apresentadas apenas
na web; a MAG mantém a lista de favoritos por tipo. Não existe hierarquia de subpastas.

## Controlo de reprodução

MAG e navegadores usam a mesma reserva exclusiva no servidor. Se já houver uma
reprodução, o segundo dispositivo recebe uma mensagem e não interrompe o primeiro.
Abrir menus, pesquisar ou atualizar o catálogo não ocupa uma reprodução.
Fechar o leitor ou pausar na web liberta a ligação. Uma sessão web abandonada
expira após cerca de dois minutos sem atividade do cliente.

Na MAG, faça **Restart portal** e confirme **r19**. As rotas antigas de reprodução
foram fechadas, para que uma versão anterior não abra streams sem reserva.
O comando e o avanço nativo seguro da r13 foram preservados. A nova passagem do
stream pelo servidor local, incluindo procura de posição na MAG física, ainda
precisa da confirmação do utilizador.

Este controlo abrange os dispositivos que usam Media Forge Lab. VLC ou aplicações
que usem diretamente os dados do fornecedor não passam por esta reserva;
mantenha-os parados enquanto usa o portal.

## Privacidade e manutenção

HTTP da MAG liga apenas ao IP LAN; HTTPS usa a porta 8443, com firewall limitada
à rede `192.168.1.0/24` no perfil Privado. Web Windows e gestão ligam apenas a
127.0.0.1. Não foram abertas portas no router. Dentro desta LAN, o serviço destina-se
a dispositivos de confiança; não existe conta individual por pessoa.

Os clientes recebem URLs locais temporários, nunca o URL de reprodução do
fornecedor. O encaminhamento serializa os pedidos ao fornecedor, incluindo
sondagem e reprodução, para evitar duas ligações sobrepostas. Não há logs de
URLs, argumentos privados ou erros completos do fornecedor.

O service worker guarda apenas HTML, CSS, JavaScript e ícones. Não guarda APIs,
catálogos, transmissões ou segmentos HLS offline. O servidor utiliza uma janela
temporária de segmentos, normalmente cerca de 40–50 segundos, removida ao terminar
a sessão; não é uma gravação. Chaves de TLS, configuração, catálogos e estado
privado ficam ignorados pelo Git em `config.local.json` e `.runtime/`.

O certificado do servidor expira em **3 de novembro de 2027**. `setup_https.py`
renova o certificado mantendo a CA existente. Requer `cryptography`, instalado
localmente em `.runtime/python-deps`; FFmpeg/ffprobe devem estar disponíveis
nos caminhos da configuração. Depois de renovar, reinicie o portal. Se o IP
mudar, atualize a configuração privada, regenere o certificado e reaplique
`configurar-web.ps1` para o novo IP/rede. Reservar este IP no router evita essa mudança.

## Verificações realizadas

- Chrome no Windows, HTTPS válido **sem ignorar erros de certificado**:
  filme, episódio e RTP 1 reais, um de cada vez, com frames descodificados e
  reprodução a avançar, resolução observada 1920×1080. O vídeo foi copiado.
  A saída áudio não foi avaliada por audição neste teste automatizado.
- Avanço real de 30 segundos num filme: voltou a descodificar imagem na nova posição.
- Durante TV real, segunda reprodução web e MAG recusadas com HTTP 409;
  fechar o leitor libertou a ligação. Nenhuma reprodução de teste ficou aberta.
- Testes locais com vídeo sintético: remux, conversão MPEG-4 → H.264, procura de
  posição, pausa/libertação/retoma no Chrome, limpeza e erro do fornecedor.
- Interface verificada a 1366×900 e 390×844; sem transbordo horizontal no telemóvel.
  Service worker ativo, cache só da interface e nenhum erro de instalabilidade
  reportado pelo Chrome.
- Regressões Python e navegação MAG, incluindo atualização sem duplicados,
  preservação em falhas, favoritos, temporadas, comando e avanço seguro.
  Painel local: reinício real confirmado, proteção de origem/token e recusa de
  paragem durante uma atualização testadas.

Por confirmar fisicamente: instalação/confiança do certificado e reprodução no
Android, apresentação final e reprodução/avanço na MAG324 com a r19. A instalação
efetiva da PWA no menu do Windows também não foi automatizada.

Comandos de regressão, nesta pasta:

```bat
run-python.bat -m unittest discover -s tests -p "test_*.py"
node tests/navigation.cjs
node --check public/web/app.js
```

Hls.js 1.7.4 está incluído localmente com licença e checksum, sem CDN em execução.
Referências: [Hls.js](https://github.com/video-dev/hls.js/releases/tag/v1.7.4),
[FFmpeg HLS](https://www.ffmpeg.org/ffmpeg-formats.html#hls).

## Interface v5 e televisões

Definições, Instalar aplicação e Abrir interface MAG têm ícones vetoriais,
cores discretas e destaque de foco. A instalação PWA continua destinada ao
navegador Windows/Android. As aplicações Samsung e Android TV são separadas:
ver [TV.md](TV.md). Usam o mesmo serviço e a mesma ligação única.

## Instalação visível — web v6

O botão Instalar aplicação está sempre disponível. Quando o navegador fornece
a instalação direta, abre o respetivo pedido; caso contrário mostra instruções
e, em HTTP LAN, os endereços local/HTTPS adequados. Cancelar não deixa um botão
sem ação. Dentro da PWA, ou após appinstalled, apresenta Aplicação instalada.
O estado instalado não é inferido de armazenamento antigo.

Validado em Chrome isolado: botão visível, ajuda em contexto seguro e HTTP LAN,
callback de instalação simulado, cancelamento, evento appinstalled e layout390px.
Não se instalou uma PWA real neste teste nem se abriram transmissões.
Referência: [evento beforeinstallprompt](https://developer.mozilla.org/en-US/docs/Web/API/Window/beforeinstallprompt_event).

## País inicial dos canais

A secção TV abre em Portugal (PT). Pode escolher outro país; na MAG, use
BACK ou MENU → Países e categorias. Filmes, séries e favoritos mantêm os
seus filtros habituais. Ao voltar à secção TV, Portugal é novamente o padrão.

## Arranque e retoma de filmes — web v8 (03/11/2026)

Corrigidas duas esperas observadas no Chrome deste Windows:

- O leitor/FFmpeg podia abrir o próximo pedido HTTP Range antes de fechar o
  anterior. O bloqueio global esperava pelo timeout, somando duas esperas de
  ~10 s. Agora o proxy termina os sockets do pedido anterior da mesma sessão
  web e só abre o seguinte depois de libertar o bloqueio. Nunca se abrem duas
  ligações ao fornecedor em paralelo. Parar também interrompe o transporte.
- Os GET/HEAD locais completos usam HTTP/1.1 persistente. O encerramento de
  cada resposta grande provocava resets/repetições no Chrome: uma leitura local
  de 624 KB podia falhar após ~19 s; na comparação persistente chegou em 24–36 ms.
  Escritas, erros e pedidos com corpo por ler continuam a fechar a ligação.
  A fila de aceitação HTTP suporta rajadas de ligações do navegador/leitor.

Metadados de filmes/episódios analisados por FFprobe são reutilizados em memória
por até uma hora, com limite de 128 entradas e chave ID+URL. Não se guarda vídeo
nesse cache. Alteração do URL, expiração e modo compatível exigem nova análise.
No modo web normal, a segunda análise FFmpeg é limitada e o alvo HLS é 2 s;
keyframes e vídeo original mantêm-se. Compatibilidade conserva análise completa.

O leitor mostra a etapa atual, desativa avanço enquanto prepara e apresenta
«—» até conhecer a duração. Não guarda progresso de uma preparação incompleta.
Um erro tardio de um pedido cancelado não substitui o estado do novo leitor.
Se a biblioteca HLS falhar ao carregar, tenta carregá-la novamente antes de
abrir a ligação ao fornecedor, com erro explícito e prazo limitado.

Teste real autorizado, uma reprodução de cada vez, no Chrome isolado:
«PT - A Maravilhosa Árvore Encantada (2026)», ID m2213260. Antes: ~24–26 s
para preparar; nas primeiras tentativas as falhas HTTP impediam a imagem.
Depois: 4,06 s até o navegador apresentar fotogramas e 3,46 s numa nova retoma
com metadados reutilizados. Imagem capturada/revista, 1920×800, vídeo original
remuxado; som não confirmado por audição. São amostras deste filme, não um
prazo garantido para todo o catálogo. O progresso guardado continuou disponível.
Os testes terminaram com a ligação ao fornecedor livre.

65 testes Python passaram, incluindo troca de Range com a resposta anterior
aberta e confirmação do fecho da origem, cache/expiração/troca de fonte,
compatibilidade, falhas, exclusão entre dispositivos, GETs grandes na mesma
ligação e fecho de pedidos com corpo por ler. Regressões MAG, TV e novo teste
web de preparação/cancelamento/progresso passaram. Aplicação ativa nesta raiz.
Atualizar o separador com Ctrl+F5 para carregar a web v8.

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

## Filtros VOD — web v10

Filmes e séries: país/idioma da versão do catálogo e género, combináveis com
categoria, pesquisa e favoritos. Todos por defeito, sem restringir a PT/BR.
Quando o fornecedor não indica género, os títulos ficam em Sem género indicado.
Atualizar com Ctrl+F5; o cache da PWA foi versionado para v10, sem cache de streams.

## Sobre — web v11

O botão Sobre no menu mostra sempre a versão da interface carregada, definida
por WEB_VERSION em app.js. O diálogo apresenta nome, logótipo, versão e modo
Navegador/Aplicação instalada (PWA). Atualizações da interface devem incrementar
esta constante e as referências/cache no HTML e sw.js em conjunto.

## Ajuda de instalação — web v12

O fallback de instalação abre os passos do navegador detetado, mantendo Chrome
Windows, Edge Windows e Chrome Android disponíveis em secções expansíveis. Links
para a documentação oficial acompanham as instruções. O caminho exato pode variar
com a versão/idioma do navegador. A ausência de beforeinstallprompt não identifica
por si só a causa nem prova que a app não esteja instalada.

Diagnóstico Chrome isolado em http://127.0.0.1:8091/web/: getInstallabilityErrors
vazio, manifesto sem erros, service worker activated e controller presente. Não
prova que o navegador/endereço do utilizador tem o mesmo estado. Ajuda verificada
com agentes de utilizador Chrome/Edge/Android simulados; não foi instalada PWA.


## Áudio e legendas — web v14

O painel **Áudio e legendas**, logo abaixo do vídeo, apresenta sempre ambos
os controlos. Áudio único ou inexistente é indicado; o seletor só permite trocar
quando há alternativas. Legendas podem ficar Desligadas ou usar uma faixa de
texto incluída no ficheiro. Nomes de idioma são apresentados em português.
As faixas não são tradução automática nem pesquisa/download de legendas externas.
Legendas de imagem (PGS/DVD/DVB) aparecem como não suportadas nesta versão;
texto já gravado na imagem não pode ser desligado.

Alterar uma faixa reinicia a preparação na posição atual, mantendo apenas uma
ligação. Se o vídeo estiver em pausa, a escolha só entra em reprodução ao retomar.
Uma única instância FFmpeg lê a origem e produz HLS e o WebVTT escolhido. Vídeo
compatível continua em remux. O sidecar é temporário, apagado ao terminar, e não
é servido diretamente nem colocado em cache offline. Cues de texto delimitados
são entregues pelo pulse autenticado da sessão; o navegador usa TextTrack/VTTCue
para suportar também o ecrã inteiro. As TVs/Pessoal usam o mesmo componente ES5,
com sobreposição quando o leitor é nativo. A MAG IPTV mantém as opções nativas
MENU → Áudio/Legendas; Pessoal na MAG usa o novo componente partilhado.

Validação sintética: duas faixas AAC com tons distintos (seleção confirmada por
análise do áudio de saída), dois idiomas de legendas, seek, desligar, limpeza,
rejeição de outro dispositivo e preservação de sessão perante parâmetros inválidos.
Chrome confirmou texto PT/EN efetivamente visível, pausa sem ligação, retoma e
biblioteca pessoal móvel. Conteúdos do fornecedor e TVs/MAG físicos ainda
precisam de confirmação humana para estas novas opções.


## Janela e ecrã inteiro — web v15

Mantêm-se os controlos nativos dentro do vídeo (pausa, som, ecrã inteiro e menu).
No cabeçalho do leitor, − e ＋ diminuem/aumentam a janela; no computador também
é possível arrastar o canto inferior direito. ⛶ e o duplo clique na imagem
usam o mesmo comando de ecrã inteiro, sem trocar a sessão nem a origem do vídeo.
O duplo clique preserva reprodução/pausa; a faixa inferior de controlos nativos
fica excluída deste gesto. O tamanho é limitado à janela do navegador.

Pausas transitórias deixam de libertar imediatamente a ligação: só uma pausa
persistente de900ms a liberta. Retomar nesse intervalo reutiliza o leitor; a
pausa prolongada mantém a política de libertar a ligação. Alterar o tamanho
não retoma automaticamente um vídeo pausado. Escape ao sair de ecrã inteiro
não fecha o diálogo através de um evento cancel simultâneo.


## Apresentação discreta — web v16

Áudio e legendas fica fechado por defeito, incluindo ao abrir outro conteúdo.
Um botão pequeno abre os seletores compactos, sem caixa colorida ou moldura.
O mesmo estilo aplica-se às TVs e Pessoal; o foco do comando continua visível.


## Vídeo flutuante no Windows — web v17

No cabeçalho do leitor, **Destacar** abre a janela Imagem na imagem do Chrome,
que pode ser movida/redimensionada e fica sobre outras aplicações. **Repor**
regressa à página. Mantém o mesmo vídeo e a mesma ligação; vídeo pausado fica
pausado. Fechar o leitor da aplicação fecha também a janela flutuante. Manter
o separador aberto; o botão aparece quando a API é suportada e ativa quando
há vídeo preparado. Teste Chrome confirmou entrada/saída e continuidade;
posição da janela sobre outras apps deve ser confirmada no Windows físico.

Testes de vídeo sintético devem iniciar o Chrome com **--mute-audio** e definir
video.muted=true antes da reprodução. Os tons de teste não devem ser audíveis.


## Mudar conteúdo dentro do leitor — web v19

Acima do vídeo: **Anterior**, seleção da **lista ativa** e **Seguinte**. Mantêm
os filtros, pesquisa, origem, categoria, qualidade, pasta de favoritos e ordem
da lista de onde abriu o conteúdo. Funciona para canais, filmes e episódios.
Anterior/Seguinte atravessa páginas; no seletor, Página anterior/seguinte permite
consultar outros conteúdos sem iniciar reprodução. São carregados apenas os
metadados da página necessária. No início/fim, a direção indisponível fica inativa.
Trocar conteúdo termina a sessão anterior antes de iniciar a próxima e guarda
o progresso do filme/episódio. Fechar o leitor invalida pedidos de lista tardios.


## Idioma inicial de filmes e episódios — web v20 / TV r17 / MAG r27

Ao abrir um filme ou episódio, a preferência de áudio é: português identificado
como de Portugal; inglês; por fim, a faixa original/default do ficheiro.
Português genérico (`por`/`pt`) não é assumido como PT-PT, porque pode ser brasileiro.
Só são selecionadas faixas existentes; não traduz nem troca por outro título.
A escolha manual em Áudio e legendas mantém-se durante pausas, retomas e avanços.
Abrir outro título ou reabrir o mesmo volta a aplicar a preferência inicial.
TV em direto, vídeos pessoais e legendas mantêm o comportamento anterior.

Web, Samsung e Xiaomi usam a mesma seleção no servidor, com os metadados já
obtidos para reproduzir, sem consulta extra ao fornecedor. MAG usa os idiomas
informados pelo leitor nativo e só muda a faixa fora dos callbacks do firmware.
Se não houver informação suficiente na MAG, mantém o áudio que o leitor escolheu.


## Barra de posição dentro do vídeo — web v21

Nos filmes e episódios, existe uma única barra dentro do vídeo, com a posição
e duração totais. Clique/arraste para escolher um ponto ou use as setas quando
a barra tem foco. Os botões de reprodução/pausa, volume e ecrã inteiro ficam
junto da barra. Os controlos desaparecem quando não estão a ser usados e voltam
ao mover/tocar no vídeo ou focar um botão; permanecem visíveis em pausa.
Em ecrã inteiro, a mesma barra continua acessível, sem reiniciar o vídeo ao
maximizar. A barra deixa de mostrar a duração parcial do trecho HLS preparado.

Escolher uma posição pede ao servidor esse ponto do ficheiro; pode haver uma
breve preparação. Em pausa, escolher a posição mantém a ligação livre; ▶ retoma
no ponto escolhido. Fechar guarda essa posição. A escolha de áudio/legendas
mantém-se. TV em direto continua com controlos nativos. Esta alteração é do
leitor web de filmes/episódios; MAG, interfaces nativas TV e Pessoal inalterados.
No modo Destacar, os controlos da pequena janela são geridos pelo navegador;
a barra completa permanece na página, não dentro da janela PiP nativa.


Origens múltiplas (web25 / TVr24): abrir Origens, marcar uma ou várias e escolher
Concluir, ou clicar fora. A lista atualiza a cada marca; a categoria mantém-se.
Todas as origens limpa a seleção. Desmarcar a última também regressa a Todas.
Comando: setas, OK para marcar/desmarcar, Voltar para fechar. Na MAGr30, MENU →
Origem dos canais usa as mesmas regras. Qualidade Auto continua a escolher uma
versão por canal entre as origens selecionadas. Não há alteração de favoritos.


Preferências persistentes (web26 / MAGr31 / TVr25): os filtros e a pesquisa ficam
guardados por secção e são recuperados ao regressar ou reabrir a aplicação. Inclui
origens múltiplas, país, categoria, género, qualidade, PT/BR e pasta de favoritos.
Cada navegador/dispositivo/endereço tem as suas preferências. Apagar os dados do
navegador remove-as; favoritos e progresso no servidor permanecem. Sem preferências,
TV começa em Portugal. A biblioteca volta à primeira página, sem iniciar reprodução.


Web27: «Destacar» liberta a biblioteca para consultar, pesquisar e escolher outro
conteúdo. No Chrome Windows com Document PiP, a mesma janela é reutilizada e o
leitor anterior é parado antes do novo. Vale para TV/filmes/séries, Coleções e
Pessoal, incluindo fotografias. Navegar pelos links da app mantém o leitor ativo;
fechar/navegar para fora da app termina o contexto. A barra inferior permite Repor
ou Parar; Repor abre a biblioteca do conteúdo destacado. Suporte completo depende
de Document PiP e contexto seguro (127.0.0.1 ou HTTPS); PiP nativo é alternativa
conforme o navegador. Nenhuma transmissão é guardada offline.


Pessoalv9: cartões compactos e60 conteúdos por página por defeito. «Por página»
no rodapé permite12/24/30/60 e fica guardado por vista. TV começa com30 e MAG24.
Nomes/pastas completos aparecem ao passar o rato; imagens usam carregamento lazy.


Pessoalv10: navegação lateral com ícones, pesquisa/filtros alinhados e estado
OneDrive compacto. «Gerir biblioteca» abre ações de pastas/atualização/conta.
No comando, → passa da secção aos conteúdos; ← na primeira coluna regressa à
secção. BACK fecha a gestão. No telemóvel, as secções passam para duas filas.
