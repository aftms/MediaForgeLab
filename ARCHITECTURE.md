# Componentes partilhados

Um único servidor Python e uma única instância de `MediaManager` servem todas
as interfaces. As apps não têm catálogos ou bases de favoritos independentes.

| Componente | Responsabilidade comum |
| --- | --- |
| `catalog.py`, `provider.py`, `refresh.py` | Catálogo completo, identificadores, pesquisa/filtros, detalhes e atualização segura |
| `favorite_layout.py`, catálogo e estado privado | Favoritos, pastas e ordenação partilhados |
| `server.py`, `storage.py` | API, progresso, persistência e acesso privado |
| `media.py` | Reserva exclusiva, FFmpeg, HLS e libertação da reprodução |
| `public/assets/` | Identidade e ícones comuns |
| `public/tv/` | Mesma interface e navegação para Samsung e Xiaomi |

A MAG usa `public/portal.js` e a API nativa gSTB. Web/PWA usa `public/web/`
com rato/toque e HLS. As TVs partilham `public/tv/player.js`, que escolhe AVPlay
Samsung ou o adaptador Java Android; os invólucros instaláveis ficam em `tv/`.
Estas diferenças são necessárias ao navegador e leitor de cada equipamento.

Há lógica de apresentação repetida entre MAG, web e TV (pedidos API, pesquisa,
navegação e renderização). Ainda não existe uma biblioteca universal de UI.
A consolidação será incremental: extrair contratos/helpers estáveis, com testes
ES5 e regressão do comando, sem impor APIs modernas ao WebKit da MAG.

Favoritos são lidos/escritos no servidor. Uma alteração afeta todas as interfaces,
mas não existe push em tempo real: outra lista já aberta pode precisar de ser
reaberta. Pastas/reordenação são geridas na web; a interface TV consulta as pastas,
e a MAG conserva a sua organização mais simples por tipo de conteúdo.

## Categorias próprias dos canais

`channel_categories.py` define a taxonomia local comum a MAG, web, Samsung e
Xiaomi: Generalistas, Desporto, Filmes, Séries e entretenimento, Infantis,
Notícias, Documentários, Música, Estilo de vida, Religião, Adultos e Outros.
Não requer serviços pagos nem consultas externas. Regras pelo nome reconhecido
precedem pistas de género dos grupos originais; grupos adultos têm prioridade.
Casos sem indicação suficiente ficam em Outros. A classificação é heurística,
podendo precisar de ajustes neste módulo para marcas não reconhecidas.

O catálogo aplica a melhor indicação a todas as variantes da mesma família,
mantendo a categoria comum entre origens e qualidades. Origem continua como
filtro separado. Os grupos originais permanecem nos dados privados e nos aliases
de consulta para clientes antigos, atualização e exportação M3U. A API apresenta
a categoria própria em `group` dos canais e em `view=groups`; filmes e séries
mantêm os seus grupos. IDs e chaves de favoritos não mudam. As regras voltam a
ser aplicadas ao carregar os catálogos atualizados. Não é necessário reinstalar
APK/WGT: reabrir a interface atualiza as listas.

## País/idioma e género de filmes/séries

`vod_filters.py` calcula dimensões locais ao carregar o catálogo: `countries`
identifica a versão por rótulos do catálogo, não o país de produção; EN mantém
Inglês / Internacional, NORDIC agrupa os países nórdicos e os casos desconhecidos
ficam explícitos. Nos grupos PT/BR, prefixos PT e BR no título distinguem versões;
sem essa distinção, o título pertence aos dois filtros. Não implica garantia da
faixa de áudio. `genres` normaliza metadados existentes, com categorias como
alternativa; não adivinha pelo título. Um título pode ter vários géneros, mas
aparece uma vez na lista filtrada. Sem dados: Sem género indicado.

API: `view=countries&kind=movie|series`, `view=genres&kind=movie|series&country=PT`
e `kind=movie|series&country=PT&genre=Ação`. Combinam com grupo, pesquisa,
favoritos e PT/BR; parâmetros devem ser URL-encoded. IDs, grupos originais,
ficheiros exportados e chaves de favoritos permanecem iguais. Não há pesquisa
externa, descarga em massa de detalhes nem novas transmissões. Os índices por
país e grupo são reconstruídos nas atualizações normais.
