# Media Forge Lab — portal MAG e biblioteca local

Portal privado na LAN, no workspace próprio `D:\Workspace\MediaForgeLab`. A box foi confirmada pelo utilizador:
**MAG324**; o portal base já foi aberto com sucesso. As funcionalidades novas
desta versão necessitam de confirmação no equipamento físico.

**r19 — aplicação web e gestão disponíveis:** [guia Windows, Android/PWA e Admin](WEB.md).
Partilha os mesmos catálogos, favoritos, progresso e atualização com a MAG.
O servidor passa a encaminhar a reprodução mediante uma reserva exclusiva,
para permitir apenas um leitor MAG/web de cada vez. Reiniciar o portal na box
para carregar a r19; o endereço permanece igual.

**Portal 1 URL:** `http://192.168.1.240:8090/`

Não é necessário voltar a escrever o endereço na MAG. Para carregar esta versão,
usar **System settings → Restart portal**.

## Apresentação Media Forge Lab

Interface sóbria em azul-escuro, com verde-água, dourado e lilás discretos por
secção. Logótipo original combina dois enquadramentos de media com o símbolo de reprodução.
Títulos e nomes em negrito, texto secundário com mais contraste e ícones com
traços mais fortes. Navegação lateral, listas com contagens e painel ilustrado.
Os 19 PNG são originais, pequenos e locais: sem fontes externas, downloads de
capas, animações ou vídeos de fundo. As ilustrações identificam a secção; não
são capas de filmes. `design-assets.py` regenera os PNG com Pillow, apenas no
desenvolvimento; o servidor continua sem dependências adicionais.

Navegação e atalhos do comando mantidos. Verificação visual em Chrome isolado
a 1280×720 e 720×576, além dos testes de navegação/ES5; a apresentação final
no WebKit da MAG exige confirmação no equipamento.

O quadro de opções usa ícones e uma descrição da seleção, mantendo a ordem e
as teclas do comando. O seletor de qualidade abre na qualidade atual, assinalada
«Em uso», e explica cada filtro, incluindo o funcionamento de Auto.

Para sair para o menu da MAG: durante **Loading portal…**, premir **MENU** e
escolher **Embedded portal**. **SETUP** abre as definições do sistema.
BACK dentro deste portal volta à lista; não abre o menu interno da box.

## Biblioteca

- **TV:** lista completa do OneDrive; países/regiões → categorias → canais.
- **Filmes:** `filmes-completos.m3u` do OneDrive; categorias, com PT/BR em primeiro.
  `filmes-pt-br.m3u` é um subconjunto, pelo que não se importa novamente.
- **Séries:** catálogo de metadados do fornecedor, guardado localmente; abrir uma
  série mostra as **temporadas**, com contagem de episódios; abrir uma temporada
  mostra apenas os seus episódios, ordenados por número e paginados. A temporada
  0 aparece como **Especiais**. BACK sobe de episódios para temporadas e depois
  para a lista de séries, mantendo a posição e a origem (incluindo Favoritos).
  A r17 consulta os detalhes apenas da série escolhida e reutiliza o cache ao
  entrar nas temporadas. Os IDs dos episódios e o progresso não mudam. Na lista
  de temporadas, Guardar/Remover favorito continua a aplicar-se à série inteira.
- **Favoritos:** comuns ao portal desta casa, guardados no computador em
  `.runtime/favorites.json`. Sobrevivem a reinícios do portal e da box.
  Um favorito TV aplica-se à família do canal, incluindo a qualidade escolhida.
  Nos episódios, a tecla de favorito guarda a série.
  Na r16, os favoritos estão separados em **Canais / Filmes / Séries** e abrem
  sempre nos **Canais**. No primeiro resultado (ou numa lista vazia), **↑**
  seleciona os separadores; **← / →** muda de tipo e **↓ / OK** volta à lista.
  Também pode usar **MENU → Tipo de favorito**. A pesquisa fica limitada ao
  tipo escolhido; ao voltar dos episódios regressa às séries favoritas.

Fontes atuais privadas:
`C:/Users/Utilizador/OneDrive/Comum/iptv/canais-completos.m3u` e
`C:/Users/Utilizador/OneDrive/Comum/iptv/filmes-completos.m3u`.
As listas continuam fora do repositório. O catálogo da box recebe páginas de
dez entradas, não as listas completas.

Os menus iniciam assim que o HTML existe, sem depender de
`window.onload`, da contagem da biblioteca ou de `InitPlayer`. O leitor nativo
só é inicializado ao pedir reprodução. Os pedidos têm limite de 15 segundos;
uma falha mostra uma mensagem e permite repetir com MENU → Atualizar esta lista.
Um carregamento incompleto do JavaScript mostra uma mensagem própria.

O PC mantém a biblioteca e índices por secção, país, categoria e família de canal.
Ao abrir um país ou categoria só consulta esse bloco; os resumos dos diretórios
são reutilizados entre páginas. A box recebe apenas a página pedida (10 entradas).
O PC continua a ler as listas locais uma vez quando o servidor arranca; não faz
essa importação a cada abertura da MAG. A causa exata da espera na versão 2 não
foi reproduzida no hardware: a correção de arranque precisa de validação na MAG.

Importação validada no computador: 56 283 entradas de TV, 973 separadores
removidos, **55 310 streams TV**, **162 749 filmes** e **37 786 séries**.
Há 73 países/regiões de TV identificados; grupos internacionais são apresentados
como tal. Contagens de canais depois do filtro Auto são inferiores porque as
versões repetidas são agrupadas. Não foi feita reprodução para testar estes números.

## Comando e pesquisa

| Tecla | Função |
|---|---|
| Vermelho / F1 | Alternar TV, Filmes, Séries e Favoritos |
| Verde / F2 | Guardar ou remover favorito da seleção / reprodução |
| Amarelo / F3 | Abrir pesquisa |
| Azul / F4 | Abrir Favoritos; dentro da pesquisa, fechar teclado e escolher resultados |
| ↑ / ↓ | Escolher; durante reprodução, mudar de canal/episódio |
| ← / → | No menu, ir ao painel esquerdo / regressar à lista; nos separadores dos favoritos, mudar de tipo; num filme ou episódio, toque de 5 segundos / manter para acelerar |
| « / » (REW / FF) | Percorrer a barra continuamente; repetir aumenta a velocidade; OK aplica, BACK cancela |
| OK | Abrir país/categoria/série ou reproduzir; a reproduzir, mostrar informação |
| BACK / EXIT | Fechar janela, parar reprodução ou voltar à lista anterior |
| MENU | Opções da biblioteca; durante o vídeo, controlos de reprodução, áudio e legendas |
| INFO | Programação e descrição do conteúdo |
| CH+ / CH− (PgUp / PgDn) | Página anterior / seguinte na lista; durante reprodução, mudar canal/episódio |
| Números + OK | Ir à posição indicada na lista atual |
| PAUSE / espaço | Pausar ou retomar no leitor nativo |
| VOL+ / VOL− / MUTE | Volume nativo da MAG |

Na r18, **←** leva da lista ao painel esquerdo. Use **↑/↓** para percorrer
TV, Filmes, Séries, Favoritos, Pesquisar, Guardar/Remover favorito, Qualidade e
Opções; **OK** ativa o botão destacado. **→** ou **BACK** regressa à mesma
seleção na lista; **TAB** também alterna os dois painéis. Escolher uma secção
com OK abre a respetiva lista. A pesquisa aplicada regressa aos resultados;
cancelar a pesquisa regressa ao painel de origem. Manter OK numa opção não
ativa repetidamente a opção ou o ecrã seguinte. Os botões mantêm os lugares e
as funções anteriores.

Também sem usar os botões de cores, na lista prima **MENU**: as primeiras opções são
**Pesquisar**, **Guardar/Remover filme/série/favorito** e **Abrir favoritos**.
Escolha com **↑/↓ e OK**. No teclado de pesquisa, **Ver lista** fecha a pesquisa
e permite escolher os resultados. Durante o vídeo, **MENU → Guardar filme/série**
guarda o favorito sem interromper a reprodução; BACK fecha o menu.

A pesquisa usa um painel compacto à direita, deixando a lista visível. Os resultados
atualizam-se 250 ms após escrever/apagar letras, pelo comando ou teclado USB.
Com o comando, escolher letras com setas e OK; Azul ou «Ver lista» fecha o teclado
para escolher um resultado. Com teclado USB, Enter passa para a lista. EXIT/CANCELAR
repõe a vista anterior. Inclui espaço, apagar e limpar; respostas antigas são
descartadas e escrever nunca inicia reprodução. É indiferente usar maiúsculas/minúsculas ou acentos
na pesquisa. Pesquisa na secção atual e, na TV, no país selecionado.
Para procurar em toda a TV, pesquisar a partir da lista de países.
Enquanto se escreve, não são feitas novas consultas EPG. Ao voltar à lista,
a programação do canal selecionado é consultada novamente; INFO abre os detalhes.

Se o teclado físico é português e a box usa US: `Shift+Ç` escreve `:`;
a tecla `-` junto ao Shift direito escreve `/`.
A MAG324 não tem Bluetooth integrado; usar USB para teclado.

## Qualidade e versões repetidas

**MENU → Qualidade**, ou botão Qualidade no ecrã:

- **Auto:** uma versão por família de canal, preferindo Full HD, HD, 4K, SD,
  qualidade não indicada e, por último, 8K.
- **SD / HD / Full HD / 4K / 8K:** apenas entradas com esse rótulo; agrupam-se
  fontes/versões da mesma família.
- **Não indicada:** canais sem rótulo reconhecido.
- **Todas as versões:** mostra as alternativas, útil quando uma fonte falha.

A identificação usa os nomes/grupos do fornecedor; não mede a resolução nem
altera o stream. O agrupamento é uma heurística de nomes (inclui prefixos
PT/MEO/NOS/VODAFONE/VO/VIP); nomes diferentes podem continuar a aparecer.
Não há transcodificação. A preferência é recordada no browser/box quando o
armazenamento local do firmware está disponível.

## EPG e metadados

A programação aparece no painel lateral após selecionar um canal e pode ser
aberta com INFO. São dados reais do fornecedor por `get_short_epg`, com cache
de cinco minutos e consultas apenas depois de a seleção parar brevemente.
Quando não há dados, aparece uma mensagem de indisponibilidade; não há grelha
inventada. Uma consulta real de RTP 1 devolveu quatro programas nesta validação.
A hora apresentada é a hora fornecida no EPG.

Catálogo/EPG/episódios são consultas de metadados, não streams de vídeo.
Não se faz download de logos, trailers ou vídeos em segundo plano.
O primeiro acesso aos episódios pode demorar enquanto a API do fornecedor responde.
O cache de consultas recentes é limitado a 64 séries. Os episódios já obtidos
ficam guardados em disco e conservam os seus IDs.

## Atualizar catálogo (versão 4)

Usar **Verificar atualizações** no topo, ou **MENU → Verificar atualizações do
catálogo**. A verificação corre em segundo plano, sem Stop/Play, sem mudar a
seleção e sem reiniciar o servidor. Mostra a fase em curso, a data UTC da última
atualização bem-sucedida e o número de canais/filmes/séries adicionados.
Repetir o botão durante a operação não inicia outra atualização.

A origem é recuperada dos URLs privados da M3U existente. Para substituir:
**MENU → Definições · URL de origem**, introduzir o URL `get.php` completo com
teclado USB ou abrir o portal no computador. O campo é do tipo palavra-passe,
fica vazio ao abrir/fechar e o servidor nunca devolve o URL nem as credenciais.
Só mostra o servidor. Guardar não consulta `get.php`: a API `player_api.php`
é usada na próxima verificação, com os parâmetros devidamente codificados.
A biblioteca ativa só muda quando todas as consultas e a gravação tiverem sucesso.

São consultados os seis endpoints de categorias/listas de TV, filmes e séries.
A comparação usa **tipo + ID do fornecedor**; nomes, categorias múltiplas,
logótipos/capas, descrições e outros metadados são atualizados. Os IDs internos,
a ordem dos títulos existentes e as chaves dos favoritos são preservados mesmo
quando o nome muda. Entradas ausentes na resposta são conservadas; não há remoção
automática. Os catálogos completos são mantidos, com PT/BR nas categorias opcionais.
As imagens são guardadas como metadados; não se descarregam capas em massa.

Os detalhes das séries são revalidados **ao abrir a série** após uma atualização,
ou após 15 minutos. A consulta usa `get_series_info`; cada URL usa o **ID do
episódio**. Novas temporadas/episódios entram sem duplicados e a interface indica
o número de episódios novos. Em falha usa os episódios guardados e avisa.

Ficheiros de saída privados em `D:\Workspace\share\IPTV`:

- `canais-completos.m3u` e `filmes-completos.m3u` completos, UTF-8.
- `catalogo-vod/portal-canais-completos.json`, `portal-filmes-completos.json`
  e `portal-series-completos.json` com os catálogos completos normalizados.
- `catalogo-vod/portal-episodios.json` e `series-episodios.m3u`, criados/atualizados
  quando se abre uma série. Esta M3U contém **apenas episódios já consultados**;
  não inventa links de reprodução para o catálogo de séries nem faz uma varredura global.

Os ficheiros são escritos e validados em temporários, com backups e um journal
de recuperação. Uma falha numa substituição repõe o conjunto anterior; um reinício
durante a operação recupera antes de carregar a biblioteca. Uma resposta vazia,
malformada ou falha de ligação cancela a atualização completa. Há uma fotografia
privada da biblioteca ativa em `.runtime/catalog-current.json`; depois da primeira
atualização esta é a fonte persistente do portal. O destino externo pode ser
configurado por `export_dir` em `config.local.json`.

Favoritos e progresso são ficheiros separados da atualização. Em filmes/episódios,
o portal guarda a posição a cada 30 segundos e ao parar; retoma após o evento de
início do leitor, se o firmware/conteúdo suportar `GetPosTime`/`SetPosTime`.
A preferência de qualidade e a navegação aberta não são reiniciadas pela atualização.
A retoma e a interface nova ainda exigem confirmação na MAG física.

## Controlos durante a reprodução

Durante um filme ou episódio, **← / →** movem a posição 5 segundos
por toque. Mantendo premido, os eventos repetidos do comando deslocam a posição
na barra: passos de 5 segundos, 10 após 1,5 segundos e 30 após 3,5 segundos.
Eventos excessivos são limitados a um por 100 ms. Ao soltar, uma única chamada
`SetPosTime` aplica a posição 200 ms depois de sair do evento da tecla, como
na versão original de saltos fixos. Nunca é chamado diretamente em keyup;
se o firmware não enviar a libertação da tecla,
900 ms sem repetição aplicam o destino. Mudar de direção reinicia a aceleração;
parar ou mudar de título cancela o destino pendente. É uma seleção progressiva
na barra, sem pré-visualização de imagens ou reprodução em velocidade acelerada.
O menu também permite saltos pontuais de 5 ou 30 segundos.
**« / » (REW / FF)** inicia uma escolha contínua da posição na barra, sem precisar
de manter a tecla. Há três níveis: 10, 30 e 60 segundos por atualização de 500 ms;
novos toques na mesma direção aumentam o nível. A direção oposta reinicia no
primeiro nível. **OK** aplica uma única mudança de posição, sempre após o
temporizador de 200 ms; **BACK** cancela a escolha e mantém o vídeo em reprodução.
As setas permitem passar para ajuste fino. A seleção é limitada ao início/fim,
e não chama Stop/Play nem o posicionamento nativo enquanto percorre a barra.
Não apresenta imagens aceleradas. O modo também está em MENU → Avançar / retroceder.
Após o posicionamento, novos pedidos aguardam a confirmação do leitor. Eventos
de descontinuidade durante o salto não são tratados automaticamente como fim
do filme. Stop e retoma não são executados dentro de callbacks nativos; o estado
é atualizado antes de chamadas que possam voltar a emitir eventos. A retoma
consome a posição guardada uma única vez. Se o leitor devolver o controlo mas não
confirmar a posição em 12 segundos, o portal volta à lista, sem abrir outra
transmissão nem marcar o filme como visto. BACK continua disponível enquanto
se aguarda. Um bloqueio completo do firmware não pode ser recuperado por um
temporizador JavaScript; a confirmação na MAG física continua necessária.
Após o relato de bloqueios em vários filmes, a revisão r12 regista checkpoints
locais antes/depois do posicionamento e da consulta da posição, eventos nativos
e a revisão carregada. `/api/player-diagnostics` só funciona na LAN com as mesmas
restrições de origem; escritas exigem o token de ação. O ficheiro privado
`.runtime/playback-diagnostics.json` retém até 128 eventos com campos estritos,
sem URLs, títulos ou credenciais. Uma falha do diagnóstico não impede o avanço.
O utilizador confirmou que os saltos antigos de 5 minutos funcionavam e que a
r12 voltou a avançar sem bloquear. Os checkpoints reais da MAG confirmaram
SetPosTime a devolver e a posição pedida atingida. A r13 acrescenta o modo rápido
sem alterar essa sequência validada; a utilização do modo rápido no comando
físico ainda necessita de confirmação.
Os saltos são limitados à duração e não enviam Stop/Play nem pedem outra URL. A duração/posicionamento
tem de ser suportada pelo ficheiro, servidor e firmware; TV em direto não tem
recuo/avanço neste portal. O painel OK mostra posição, duração e barra de progresso.

**MENU durante o vídeo** abre opções de reprodução: pausa/retoma, saltos,
idioma do áudio, legendas, som/volume, informação sobre qualidade e detalhes.
As faixas são lidas da MAG após os eventos de preparação/início. Só se oferecem
PIDs existentes; áudio usa `SetAudioPID`, legendas usam `SetSubtitlePID` e
`SetSubtitles`. Um ficheiro sem faixas selecionáveis mostra uma mensagem;
legendas gravadas na imagem não podem ser desligadas. Descritores nativos antigos
com chaves sem aspas são interpretados como dados, sem `eval`. Listas longas
de faixas são paginadas em grupos de oito.

VOL+/VOL− e MUTE controlam o som da MAG. As variantes ALT dos botões multimédia
da Infomir são distinguidas dos botões coloridos. Pausa, faixas e volume não
reiniciam a reprodução. Números durante filmes/episódios não mudam de título.

**Verde / Guardar filme / Guardar série** adiciona ou remove o título dos favoritos.
Durante um episódio, guarda a série inteira. **Azul / Favoritos** abre a seleção
conjunta de canais, filmes e séries; abrir uma série favorita mostra os episódios.
Os favoritos ficam guardados no servidor e são preservados nas atualizações.

A qualidade do filme é a do ficheiro fornecido. O filtro de qualidade da TV
não muda a resolução do filme nem recomprime vídeo; outra versão deve ser
escolhida no catálogo. Não há seleção fictícia de qualidade durante o vídeo.

Verificação no computador: leitor nativo simulado, toque, repetição/aceleração,
libertação e fallback sem keyup, limites/cancelamento, teclas ALT, favoritos de
filmes/séries/episódios persistentes, áudio/legendas/ausência de faixas, falhas de métodos,
volume/silêncio e preservação da reprodução. Reprodução, repetição do comando, procura temporal e
troca real de faixas ainda requerem confirmação na MAG física.

## Uma ligação simultânea

Abrir o menu ou manter o servidor no computador ligado não abre streams IPTV.
Cada reprodução/troca chama Stop e espera pelo menos um segundo antes de Play;
trocas ultrapassadas são canceladas. Não há pré-visualização ou retry automático.

Antes de usar VLC/outro dispositivo, carregar em **BACK na MAG para parar e
regressar à lista**. Pausa e standby podem manter o stream. O fornecedor pode
demorar a libertar a ligação e define a sua própria política; este portal não
controla outros leitores nem garante a contabilização no lado do fornecedor.

## Iniciar / parar / atualizar

Por duplo clique nesta pasta:

- `iniciar-portal.bat`: servidor oculto/em segundo plano; repetir com o servidor
  ativo não cria outro.
- `parar-portal.bat`: para apenas a instância cuja identidade foi confirmada.
- `estado-portal.bat`: mostra estado e endereço.
- `atualizar-biblioteca.bat`: pede a mesma atualização transacional de TV/filmes/
  séries ao portal ativo e mostra o resultado. Não precisa de parar/iniciar.
- `configurar-rede.bat`: regra TCP 8090, IP local 192.168.1.240, origem
  192.168.1.0/24, apenas perfil Privado. A elevação é confirmada pelo UAC.

O auxiliar usa o Python 3.10 instalado nesta máquina, com fallback para o launcher
`py`. Não exige instalação de pacotes Python.
O arranque pode levar alguns segundos devido ao tamanho do catálogo.
O computador tem de estar ligado e sem suspensão. Não foi configurado arranque
automático do Windows ou reserva DHCP; depois de reiniciar o PC, usar Iniciar.

A configuração privada é `config.local.json` (ignorada por Git). Após alterar uma
M3U inicial, parar/iniciar o portal para reler enquanto não existir a fotografia
atualizada; depois usar Verificar atualizações. Não é necessário reiniciar/recompilar o
Gateway, o Admin, o tray ou reimportar schema.

## Proteção dos favoritos (r15)

A tecla de favoritos ignora repetições rápidas e pedidos sobrepostos. Para uma
nova alteração no mesmo título, deixe passar 700 ms sem repetir a tecla.
O servidor guarda a lista, a cópia anterior (`favorites.backup.json`) e as últimas
32 alterações (`favorites.history.json`) numa transação recuperável. Estes
ficheiros ficam na pasta privada `.runtime/`; o histórico contém identificadores
e estados, sem URLs ou credenciais. Não permite reconstruir alterações anteriores
à r15. A leitura de um ficheiro inválido falha explicitamente, preservando-o,
em vez de o substituir por uma lista vazia. Uma falha de escrita repõe o estado
anterior e não altera os favoritos em memória.

## Segurança

O código fica neste repositório; listas, configuração, favoritos e caches ficam
fora do Git. Credenciais de API são deduzidas em memória a partir da M3U.
O cache antigo `library.json` guarda só metadados. A fotografia atualizada,
as listas e a configuração de origem contêm URLs/credenciais privadas e nunca
são servidas por HTTP nem incluídas em Git. `.runtime/` é ignorada por Git.
As URLs de streams só são entregues à MAG quando há uma seleção para reproduzir.

Só se ouve no endereço LAN configurado, com validação de rede, Host e Origin.
Favoritos, atualizações, origem e progresso exigem um token de ação enviado por XHR da mesma origem; a paragem
exige outro token, local. Rotas estáticas são uma allowlist, sem servir M3U,
configuração, cache ou o resto do repositório. Pedidos/URLs não são registados.
As APIs externas são restritas a ações de leitura de metadados; não seguem
redirecionamentos nem enviam credenciais através de proxies do ambiente.

Não há túnel, UPnP ou exposição pública. HTTP não protege os dados contra outros
participantes da LAN: usar uma rede de confiança. A firewall foi aplicada apenas
ao perfil Privado e à sub-rede indicada. Logs internos da MAG estão fora do
controlo deste servidor.

## Compatibilidade / validação

HTML4, JavaScript ES5 e CSS simples, sem frameworks, fetch, Promise, módulos,
flex/grid ou recursos gráficos externos. Reprodução pela API nativa
`gSTB.InitPlayer / Stop / Play`.

A **MAG324** suporta H.264 e HEVC Main/Main10 até 1080p60 conforme as suas
especificações; não é uma box 4K. Um rótulo 4K/8K do catálogo não significa
que esse conteúdo possa ser reproduzido neste hardware. Áudio, bitrate,
TLS/certificados e firmware também podem limitar determinados streams.
Não se altera firmware, não se contornam bloqueios de operador e não se
emula Stalker/Ministra.

Testes no computador:

```text
python -m unittest discover -s tests -p 'test_*.py' -v
node tests/navigation.cjs
```

Cobrem paginação, país/região, qualidade/deduplicação, pesquisa sem acentos,
favoritos persistentes e proteção da mutação, episódios/temporadas, EPG,
navegação por comando/teclado, respostas ultrapassadas, Stop/Play e erros.
HTTP real e metadados do fornecedor foram verificados sem abrir vídeos.
Transformação do JavaScript com alvo ES5 passou.
A reprodução de TV/filmes/episódios e as novas teclas exigem aceitação na MAG física.

Referências:
[Miniportal Infomir](https://wiki.infomir.eu/eng/set-top-box/for-developers/stb-linux-webkit/api-stb-application-development/examples-of-using-api-functions),
[API gSTB](https://soft.infomir.com/stbapi/JS/v343/gSTB.html),
[API antiga, teclas/eventos](https://soft.infomir.com/mag250/Doc/JS_API_MAG200_(Rev_1.20).pdf),
[Portal externo](https://wiki.infomir.eu/eng/set-top-box/stb-linux-webkit/embedded-portal/external-portal-loading),
[MAG324](https://www.infomir.eu/eng/products/archive/mag324/),
[implementação Xtream de referência](https://github.com/tellytv/go.xtream-codes/blob/master/xtream-codes.go).

## Workspace e continuidade

Código ativo na raiz deste repositório; projeto Gateway `mediaforgelab`.
Ver [TV.md](TV.md), [MIGRATION.md](MIGRATION.md) e [HANDOFF.md](HANDOFF.md).
A versão desktop antiga está arquivada localmente, sem integração automática.
