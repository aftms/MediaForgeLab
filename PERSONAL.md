# Biblioteca pessoal — primeira versão

A secção **Pessoal** usa a mesma biblioteca e interface em web/PWA, Samsung,
Xiaomi/Android TV e MAG. Os álbuns, favoritos e progresso ficam no computador
MediaForgeLab e são comuns aos dispositivos da rede de casa.

## Ligar o OneDrive pessoal

1. Usar um registo próprio no Microsoft Entra que aceite contas Microsoft pessoais.
   O Application (client) ID é público; não é a palavra-passe nem um client secret.
2. Em **Authentication → Advanced settings**, permitir **public client flows**.
   Esta aplicação usa device code; não precisa de client secret nem redirect URI.
3. Permissões Microsoft Graph **delegadas Files.Read e Files.Read.All**,
   esta última incluída por pedido explícito do utilizador. O pedido também inclui
   `offline_access` para renovar a autorização sem repetir o início de sessão.
4. Na MediaForgeLab: **Pessoal → Ligar OneDrive**, introduzir o Client ID.
   Abrir o endereço Microsoft apresentado, introduzir o código temporário e
   confirmar a conta e a permissão. A palavra-passe só é introduzida na Microsoft.
5. **Escolher pasta**, entrar numa pasta pequena de teste e escolher **Incluir
   esta pasta**. Depois **Atualizar biblioteca pessoal**.
6. Confirmar fotografias e vídeos dessa pasta antes de incluir outras pastas.

O registo não requer Entra P1/P2. A documentação Microsoft pede uma conta Azure
com subscrição ativa e um diretório para criar o registo; pode ser uma conta
Azure gratuita. Microsoft 365 pessoal e o registo técnico são coisas separadas.
Não foram ativados recursos Azure pagos por esta aplicação.

Referências oficiais:
- https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app
- https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-device-code
- https://learn.microsoft.com/en-us/graph/api/driveitem-get-content?view=graph-rest-1.0
- https://www.microsoft.com/en-us/security/microsoft-entra-pricing

## Utilização

Na MAG, **Pessoal** é uma secção do menu principal (r25), com o mesmo formato
visual das restantes secções. A seleção pelo comando tem contorno dourado.
Na biblioteca pessoal (v4), as setas percorrem as fotografias/vídeos em grelha;
OK abre o conteúdo. Os botões Favorito/Álbum nos cartões continuam clicáveis,
mas as setas não saltam para eles. Para essas ações, usar MENU/INFO ou subir
acima da primeira fila até **Opções do item** e premir OK. Depois de alterar
um favorito, a seleção regressa ao mesmo conteúdo. BACK fecha as opções.


Fotografias/vídeos, pesquisa por nome/pasta, filtros por ano e pasta, favoritos,
álbuns manuais e continuar a ver. Criar, renomear ou apagar álbuns não altera
os ficheiros originais. Fotografias em ecrã inteiro, anterior/seguinte e
apresentação automática; vídeos com pausa/retomar, avanço/recuo de 10 segundos
e barra de posição. No computador/telemóvel, arrastar e largar escolhe o ponto.
No comando, focar a barra com as setas, usar ←/→ e confirmar com OK; BACK cancela
a seleção. Se estiver em pausa, escolher outra posição mantém a pausa. Durante
a preparação ou sem duração conhecida, a barra fica desativada. A mudança pode
precisar de alguns segundos para preparar o novo ponto no servidor.
O comando permite usar setas, OK, BACK e teclado no ecrã. CH +/− muda de página.

Web Windows: `http://127.0.0.1:8091/web/personal/?client=web`.
Web HTTPS/Android: `https://192.168.1.240:8443/web/personal/?client=web`.
TV e MAG: opção **Pessoal** na aplicação. A página web permanece dentro do
âmbito da PWA instalada. O computador precisa de permanecer ligado.

## Dados e reprodução

- Só leitura no OneDrive. Seleção explícita de pastas, sem indexar a conta toda.
- Catalogação de metadados paginada, sem descarregar vídeos originais. IDs estáveis
  por drive/item, atualização numa transação SQLite depois de validar todas as
  pastas. Falhas, paginação repetida, mudança de cTag durante a leitura ou uma
  resposta inesperadamente vazia preservam os dados anteriores.
- Itens ausentes de uma leitura concluída ficam indisponíveis; organização e
  progresso permanecem guardados. Não se apagam originais nem registos pessoais.
- Os vídeos passam progressivamente pelo PC e são servidos por HLS local.
  H.264 compatível é remultiplexado; formatos incompatíveis ou resoluções acima
  de 1080p são adaptados. Avançar ou retomar inicia HLS na posição pedida.
- Uma reprodução pessoal de cada vez, separada da única reprodução IPTV. A
  exclusão entre dispositivos mantém-se para cada origem. A capacidade real do
  PC para duas adaptações simultâneas ainda precisa de avaliação com ficheiros reais.
- Cache temporário HLS limitado e removido ao parar; fotografias JPEG/miniaturas
  limitadas a 400 ficheiros/128 MB. Nada pessoal entra no cache offline da PWA.
- Tokens Microsoft cifrados com Windows DPAPI do utilizador que executa o serviço.
  `.runtime/personal/` é privado e ignorado por Git. URLs cloud e tokens nunca
  chegam aos dispositivos. Desligar conta remove a autorização local, preservando
  a biblioteca; para revogar o consentimento na Microsoft, usar a gestão da conta.

## Limites e validação

Conta real autorizada e pasta piloto indexada (18 fotografias e 1 vídeo).
Duas fotografias reais foram abertas e descodificadas no Chrome após corrigir
a resolução de URLs do OneDrive pessoal.
Testes sintéticos validam atualização repetida/falha, preservação de organização,
DPAPI, fronteiras HTTP/CSRF/Origin, streaming HLS, remux/transcode, procura de posição,
limpeza e exclusão de duas reproduções pessoais. Chrome confirmou vídeo sintético
com imagem, pausa/retomar/avanço, fotografias em várias páginas, álbuns, favoritos,
pesquisa, largura móvel e navegação simulada de comando.

Os testes sintéticos não equivalem à reprodução física MAG/Samsung/Xiaomi.
A autorização, indexação piloto e fotografias OneDrive reais já foram verificadas;
o MP4 piloto também foi descodificado no Chrome até ao fim, com arranque em cerca
de 5 segundos e sem recompressão. Som audível e dispositivos físicos continuam
por confirmar. A página Pessoal v2 prefere HLS.js/MSE quando disponível, mantendo
HLS nativo como alternativa para navegadores sem MSE.
Dependem ainda da conta, codecs, rede, firmware e capacidade do PC. MAG tem saída
até 1080p. HEIC/RAW e outros formatos de imagem usam miniatura do OneDrive quando
não são diretamente convertíveis; não se garante apresentação do original em
resolução completa. Atalhos partilhados entre drives são ignorados nesta versão.
A atualização é uma leitura completa das pastas escolhidas, não sincronização
contínua/delta. Não inclui IA, reconhecimento facial ou edição de originais.

## Desenvolvimento

- `onedrive.py`: autenticação, cofre e Graph apenas leitura.
- `personal.py`: catálogo, organização, imagens e adaptador do leitor comum.
- `public/tv/personal.*`: interface ES5 partilhada; a web usa aliases sob `/web/personal/`.
- `media.py`: pipeline comum, com namespace e limite de resolução configuráveis.
- `tests/personal_fixture.py`: servidor isolado só com dados sintéticos. Aceita um
  caminho JSON para publicar o endereço; criar `<caminho>.stop` termina-o.
- `tests/personal-browser.cjs <fixture.json> <perfil-Chrome-CDP>`: teste real no
  Chrome isolado com DevToolsActivePort. Fecha esse navegador ao terminar.
