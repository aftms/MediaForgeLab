# Media Forge Lab — nova base, 03/11/2026

O utilizador escolheu o portal MAG/web/TV como base da aplicação unificada.
O código foi extraído de `GatewayForgeLab/apps/mag-portal` para a raiz deste
workspace. Não se importou a interface desktop antiga nem o respetivo roadmap.

## Arquivo recuperável

`archive/legacy-20261103/` contém a antiga solução MediaCatalog completa,
builds, scripts, documentação, backups e handoff. `WORKSPACE-MANIFEST.json`
regista nomes e tamanhos verificados antes/depois da movimentação. A pasta é
privada e ignorada pelo Git. Inclui cópia dos ficheiros de dados locais em
`local-appdata/`; os originais em `%LOCALAPPDATA%/MediaCatalog` permanecem intactos.
Fotografias e vídeos pessoais não foram movidos nem importados.

## Avaliação inicial

Possíveis referências futuras: indexação local, miniaturas FFmpeg, coleções,
duplicados e adaptadores de casting. Não está demonstrado que compense reutilizar
esses componentes C#/Avalonia nesta aplicação Python/web. Nenhum foi integrado.
Escolheremos uma funcionalidade de cada vez com o utilizador.

## Dados e operação

Catálogos, favoritos, progresso, certificados HTTPS e assinatura/chave TV foram
copiados privadamente. O serviço continua em 8090, web Windows em 8091, gestão em
8092 e HTTPS em 8443. Não podem correr duas instâncias: existe apenas uma reserva
de reprodução por serviço. O serviço antigo tem de parar antes de iniciar este.
Os IDs técnicos das apps TV e a CA existente são preservados para atualização.
O `.env` deste projeto foi preservado; não se copiaram credenciais URG.

Fonte histórica: commit URG `a7fa295`. O arquivo legado não tem baseline Git anterior.
