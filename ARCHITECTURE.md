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
