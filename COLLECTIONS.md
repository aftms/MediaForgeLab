# Coleções — módulo v9

Biblioteca partilhada de links para vídeos, organizada por categorias/subcategorias
e listas de reprodução. Os dados pertencem ao serviço MediaForgeLab; web, MAG e
TVs usam a mesma API e base SQLite, sem bibliotecas separadas.

## Utilização

- Web: `http://127.0.0.1:8091/web/collections/?client=web` no computador servidor;
  `http://192.168.1.240:8090/web/collections/?client=web` nos outros dispositivos.
  A entrada Coleções está no menu da aplicação/PWA. Também funciona sob o HTTPS
  já configurado no portal, dentro do âmbito `/web/` da PWA.
- Samsung: abrir Media Forge Lab, versão TV r30 / pacote 1.0.30, e escolher Coleções.
- MAG: Restart portal, confirmar r29 e escolher Coleções. O menu, a biblioteca e
  a organização estão incluídos; leitores externos dependem do WebKit da box.
- Xiaomi: requer APK 1.4 para os leitores externos. O pacote está construído em
  `.runtime/tv-build/MediaForgeLab-AndroidTV.apk`; instalação pendente porque a TV
  estava desligada. O APK antigo mantém os pedidos externos bloqueados.

A **gestão fica apenas na web**: guardar/importar/editar/eliminar vídeos,
categorias, etiquetas e listas. MAG e TVs permitem consultar, pesquisar, filtrar
e reproduzir. **Guardar/retirar favoritos funciona em todas as versões**, assim
como a gravação automática do progresso. Não é necessário classificar nas TVs.

Em **Guardar vídeo**, colar um link público e, opcionalmente, título/notas e
categorias. YouTube e Vimeo tentam obter título/autor pelo oEmbed oficial. Os títulos em
falta nos links importados são obtidos em segundo plano, sem bloquear a biblioteca
nem substituir nomes escritos pelo utilizador. Se falhar, pode escrever o título
ou usar «Obter título da origem» no editor. No Facebook, páginas públicas podem fornecer
título e capa via metadados Open Graph. Não é necessário iniciar sessão na rede social.

Em **Categorias**, criar categorias, subcategorias ou mudar a categoria mãe.
Uma categoria inclui os vídeos das suas descendentes. Eliminar uma categoria
não elimina os vídeos; primeiro é necessário mover/eliminar as subcategorias.

Em **Listas de reprodução**, criar uma lista. Nas **Opções** de cada vídeo,
adicioná-lo a uma lista; dentro da lista, usar **Subir**, **Descer** ou **Retirar**.
Uma lista suporta até 500 entradas. Pode repetir um vídeo numa sequência, com
posição guardada separadamente para cada ocorrência. A edição da lista é feita na web. O vídeo existe uma única
vez na biblioteca. A ordem em reprodução é uma fotografia da lista ao abri-la.

**Reproduzir lista** retoma a última entrada; Anterior, Seguinte e o seletor do
leitor permitem escolher outra entrada. O fim confirmado pelo leitor avança
automaticamente. Favoritos, pesquisa e Continuar a ver usam os dados partilhados.
O progresso é gravado durante a reprodução e ao fechar/pausar; uma falha abrupta
de energia ou rede pode perder os últimos segundos ainda não enviados.

O comando usa setas/OK/Voltar. OK numa caixa abre o teclado do módulo; OK num
seletor permite alterar a opção e outro OK confirma. Voltar regressa ao leitor,
à biblioteca ou ao portal conforme o contexto. Criar/colar links no computador
é normalmente mais cómodo; ficam imediatamente disponíveis nos outros dispositivos.

## Etiquetas e janela destacada

Em **Opções → Editar / categorias → Etiquetas**, escrever termos separados por
vírgulas, por exemplo `workout, exercício, mobilidade` ou
`culinária, receita, sobremesa`. Um vídeo pode ter até 20 etiquetas. Diferenças
de maiúsculas e acentos não duplicam a mesma etiqueta. Pode selecionar uma
etiqueta no filtro ou clicar nela no cartão; a pesquisa também encontra etiquetas.
Em **Gerir etiquetas**, pode criar uma etiqueta antes de a atribuir, renomeá-la
globalmente ou eliminá-la. Renomear mantém as associações e o identificador;
eliminar retira apenas a classificação, preservando vídeos, favoritos e progresso.
Nomes que colidem com uma etiqueta existente são recusados, sem fundir dados.

Categorias e etiquetas podem ser combinadas. As etiquetas são partilhadas entre
web, MAG e TVs. Editar/retirar etiquetas num vídeo preserva os restantes vídeos.

Na web, **Destacar** abre uma janela sempre à frente; **Repor** devolve-a à página.
Vídeos diretos usam o Picture-in-Picture nativo, mantendo a mesma fonte. Os leitores
YouTube/Vimeo/Facebook usam Document Picture-in-Picture quando disponível, com
pausa/retoma/seguinte para as origens que suportam esses controlos. Ao mudar um
iframe de janela o navegador recarrega-o: YouTube/Vimeo retomam na última posição
conhecida; Facebook não fornece esse controlo e pode recomeçar.

É necessário um navegador desktop compatível e contexto seguro: no computador
servidor funciona em `127.0.0.1`; na rede usar o HTTPS configurado e certificado
de confiança. O botão explica quando o navegador/endereço não disponibiliza PiP.
A janela fecha com o leitor ou a página. Não é criado um segundo leitor em paralelo.

## Reprodução e limites

| Origem | Primeira versão |
| --- | --- |
| YouTube | IFrame Player API oficial, pausa/retoma/posição/fim e sequência automática. Reprodução real confirmada no Chrome e Samsung. Alguns vídeos proíbem incorporação ou exigem autenticação. |
| Vimeo | SDK oficial, com controlos e eventos quando o vídeo permite incorporação. O carregamento está implementado; reprodução física ainda não confirmada. |
| Facebook | Plugin oficial de vídeo público. Controlos dentro do plugin; passagem ao seguinte manual. Carregar o iframe não é interpretado como reprodução nem como fim. Vídeos privados/restritos podem não abrir. |
| Instagram, TikTok e outros | Links organizados; abrir na origem no computador/telemóvel. Não há extração de transmissões ou descarga. |
| MP4/WebM/HLS públicos | Reprodução direta no navegador, HLS.js quando aplicável, ou leitor nativo MAG/Samsung. Depende de formato, HTTPS/CORS e capacidade do dispositivo; não há nova transcodificação neste módulo. |

Na MAG, a compatibilidade dos leitores sociais modernos **não está confirmada**.
Se o serviço não abrir, o mesmo vídeo continua disponível em Coleções no computador
ou telemóvel. A opção Abrir na origem nas TVs explica este percurso; não promete
abrir aplicações externas que a plataforma não disponibiliza.

Nenhum vídeo é descarregado ou guardado no cache offline da PWA. Estes leitores
não usam a conta IPTV nem alteram a exclusão de reprodução simultânea do fornecedor.
A lista fecha o leitor anterior antes de abrir o seguinte. Acesso ao conteúdo
social continua sujeito às regras, disponibilidade e restrições da respetiva origem.

## Importação

**Importar links** aceita até 100 links por vez (um por linha) ou um array JSON
com `url`, `source_url` ou `video_url`, `title` ou `name` e, opcionalmente,
`tags: ["workout", "mobilidade"]`. Valida todo o lote numa
transação: um link inválido não deixa uma importação parcial. Se houver uma categoria
selecionada, aplica-a aos itens do lote. IDs conhecidos das plataformas são
normalizados; URLs curtos opacos, como `fb.watch`, não são resolvidos nem associados
automaticamente ao ID longo do mesmo vídeo.

A importação direta do HealthForgeLab não foi ativada: as capacidades atuais do
projeto MediaForgeLab devolvem `resource_access.api_services=[]`. Não foram usadas
credenciais de outro projeto. Até existir acesso autorizado a um endpoint de
exportação, usar uma exportação fornecida pelo utilizador ou colar os links.

## Manutenção e validação

- Código: `collections_store.py`, `public/tv/collections.*` e
  `public/tv/collection-player.*`; aliases web reutilizam os mesmos ficheiros.
- Dados privados: `.runtime/collections/collections.sqlite`, fora do Git.
  Para uma cópia de segurança simples, parar o portal e copiar esta pasta.
- API LAN: GET/POST `/api/collections`, com verificações de origem/Host e token
  de ação nas escritas; Samsung instalada usa também a chave privada de TV.
- Leitor externo: `/collections/player`, shell estático sem dados da biblioteca,
  credenciais do fornecedor ou chave TV. CSP/referrer próprios para os leitores
  oficiais; a política do restante portal permanece restrita.
- Android 1.4: WebView separada, sem qualquer JavaScriptInterface, para Coleções.
  A ponte nativa IPTV permanece apenas na WebView original restrita ao servidor.
- Testes: 91 testes Python passaram, incluindo 10 de Coleções (deduplicação,
  persistência, ciclos de categorias, ordenação, progresso por entrada, rollback
  proteção HTTP, etiquetas e títulos automáticos). Regressões MAG, API/AVPlay TV e filtros de origem passaram.
- Chrome isolado/silencioso: CRUD, pesquisa, favoritos, layouts 390/1280/1920px,
  navegação MAG/TV simulada, teclado e fecho do leitor passaram. YouTube real:
  tempo a avançar, pausa, retoma, salto ao fim e passagem automática ao seguinte.
- Samsung física: pacote instalado; YouTube real sem som, tempo a avançar,
  pausa/retoma, navegação, teclado e Voltar confirmados por inspeção remota.
  O item temporário foi eliminado e o leitor fechado. Captura de ecrã do debugger
  ficou sem resposta; foi interrompida sem alterar o resultado dos testes do leitor.
- Chrome real, sem som: YouTube em Document PiP com pausa/retoma, reposição na
  página e posição preservada; MP4 público em PiP nativo sem trocar a fonte; etiquetas
  editadas pela interface, normalizadas e filtradas. Fechar remove janela e iframe.
- Uma execução concorrente com builds falhou num teste sintético de transcodificação
  do Pessoal; o teste isolado passou e a repetição completa, sem builds, passou91/91.
  Nenhum código do pipeline Pessoal foi alterado por causa dessa falha.
- Xiaomi/MAG físicas e Vimeo real: confirmação pendente. Facebook real validado no Chrome na v5; TVs físicas ainda por confirmar.

Referências oficiais: [YouTube IFrame API](https://developers.google.com/youtube/iframe_api_reference),
[YouTube oEmbed](https://www.youtube.com/oembed),
[Vimeo Player SDK](https://github.com/vimeo/player.js),
[Facebook Embedded Video](https://developers.facebook.com/docs/plugins/embedded-video-player/).

Referência PiP: [Document Picture-in-Picture](https://developer.chrome.com/docs/web-platform/document-picture-in-picture).


Evolução proposta (ainda não implementada): grupos/subetiquetas até três níveis,
com filtro por pai a incluir descendentes. A versão atual usa etiquetas planas e
categorias hierárquicas, preservando a liberdade de combinar vários temas.


Validação adicional da v3: 12 testes Coleções passaram, incluindo renomeação global
de etiquetas, dados preservados e recusa de gestão nos modos TV/MAG, com favoritos
e progresso permitidos. No Chrome, gestão web e modos de consulta TV/MAG simulados
passaram sem reproduzir vídeos. A chave da app Samsung não pode alterar a biblioteca
por esta API; os pedidos dos clientes hospedados também indicam o modo de utilização.

Categorias versus etiquetas: a proposta atual é usar categorias para temas amplos
(Exercício, Culinária...) e etiquetas para características combináveis (Mobilidade,
Força, Glúteos, Sobremesa...). Não foi reorganizado automaticamente o conteúdo do
utilizador. A hierarquia de etiquetas e filtros com descendentes continua em análise.

A v4 reduz os títulos dos cartões e o espaçamento entre linhas, com tamanhos adequados a web/telemóvel, MAG e TV.


## Facebook — capa e enquadramento (v5)

O serviço tenta obter título/capa dos metadados públicos da página, incluindo para
vídeos anteriormente guardados. Só acede por HTTPS a hosts Facebook permitidos e
imagens fbcdn.net, com limites de redirecionamentos, tamanho e tempo. Não usa
sessões, cookies, tokens da rede social nem extrai transmissões. Páginas privadas,
recusadas ou indisponíveis mantêm o título/capa existente e o símbolo de alternativa.

A imagem é validada e reduzida a PNG, guardada na mesma SQLite privada com a
proporção de apresentação. A biblioteca referencia uma imagem local versionada,
evitando guardar nos clientes o endereço temporário do CDN. Favoritos, etiquetas,
categorias, listas e progresso permanecem intactos; nomes manuais não são substituídos.
O endpoint GET/HEAD `/collections/image/col-<id>` admite imagens nas TVs sem chave
em URL, mantendo as verificações LAN/Host; não permite consultar a biblioteca.

O leitor oficial fica centrado e ajustado ao espaço disponível, mantendo a proporção
da capa (ou dimensões explícitas do vídeo quando fornecidas). Redimensionar a página
ajusta apenas a apresentação, sem recarregar o iframe. «Enquadramento» permite
escolher vertical, horizontal ou quadrado se os metadados não representarem o vídeo.
Facebook continua com controlos próprios, avanço manual na lista e sem progresso
confirmado por API. Destacar pode reiniciar o iframe, como anteriormente.

Chrome isolado e sem som: capa local 360×640 visível; vídeo real 720×1280 inteiro,
tempo a avançar e continuidade ao passar de janela 1400×1000 a 390×844. Screenshots
inspecionadas. Unidade/HTTP: obtenção pública, bloqueio de URLs/redirecionamentos
externos, resposta indisponível, persistência, migração de DB e dados preservados.
Sem reproduções do fornecedor IPTV. Compatibilidade Facebook nas TVs/MAG físicas
ainda depende do respetivo leitor e não foi confirmada nesta fase.


Validação v5: 7 testes de metadados e 13 de Coleções passaram. Bateria completa:
100 dos 101 passaram; teste sintético do pipeline Pessoal falhou de forma
intermitente e passou na última repetição isolada. O mesmo teste na baseline HEAD
também passou; o pipeline e o seu teste não foram alterados. Regressões MAG/TV
passaram. Enquadramento manual, ecrã inteiro, janela destacada e reposição também
confirmados no Chrome. Serviço ativado sem reprodução ativa; Samsung1.0.23 instalada.


A v6 recupera pesquisa e filtros (categoria, etiqueta, plataforma e lista) ao reabrir
o módulo no mesmo navegador/endereço. Referências removidas são descartadas sem
perder os restantes filtros. Não inicia automaticamente vídeos.


v7: destaque e navegação usam o controlador web comum. A biblioteca fica livre e
escolher outro conteúdo substitui o atual na mesma janela quando há Document PiP.
Os links da app permitem passar entre Coleções, Pessoal e TV mantendo o controlador
residente. MP4 usa a mesma superfície destacada; embeds podem recarregar ao mudar
de janela. YouTube retoma a posição, Facebook continua com controlos próprios.


A v8 usa títulos compactos de duas linhas (web12px, MAG13px, TV14px), com nome
completo ao passar o rato. Os nomes guardados permanecem completos.


## Por classificar

Categoria automática que aparece sempre, mesmo vazia. Reúne vídeos sem categorias;
atribuir uma categoria retira-os daqui, remover a última volta a incluí-los. Ter
etiquetas não altera esta regra. Pode combinar este filtro com pesquisa e favoritos.
A categoria não pode ser editada, apagada ou usada como mãe de subcategorias.
No editor, deixar todas as categorias desmarcadas equivale a Por classificar.
API: GET `/api/collections?category=uncategorized`; o nó é virtual (`system:true`),
não fica gravado nas associações do vídeo. Nomes, favoritos e progresso preservados.
