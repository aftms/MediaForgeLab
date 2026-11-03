"""Local live-TV taxonomy; no network calls or changes to supplier metadata."""
import re

CATEGORIES = ('Generalistas', 'Desporto', 'Filmes', 'Séries e entretenimento',
              'Infantis', 'Notícias', 'Documentários', 'Música', 'Estilo de vida',
              'Religião', 'Adultos', 'Outros')

# Specific channel names precede broad provider-group hints. Keep these rules
# central so a correction applies to MAG, web and both TV applications.
NAME_RULES = [
    ('Adultos', r'\b(?:XXX|PLAYBOY|HUSTLER|BRAZZERS|DORCEL|PENTHOUSE)\b'),
    ('Desporto', r'\b(?:DAZN|ELEVEN|SPORTS?|SPORTING|SPORTV|EURO\s?SPORT|BTV|BENFICA|ESPN|NBA|NFL|NHL|MOTOGP|F1|FORMULA\s*1|ONETORO)\b|^11$|^A BOLA\b'),
    ('Infantis', r'\b(?:PANDA|BIGGS|CARTOON|CARTOONITO|NICKELODEON|NICK\s*(?:JR|JUNIOR)|BABY\s?TV|DUCK\s?TV|LOLLY KIDS|KIKA|KANUCA)\b|^SIC K$|\bDISNEY (?:CHANNEL|JUNIOR|XD)\b'),
    ('Filmes', r'\b(?:TVCINE|CINEMUNDO|HOLLYWOOD|MOVIES?|CINEMA|CINE)\b'),
    ('Documentários', r'\b(?:DISCOVERY|NATIONAL GEOGRAPHIC|NAT GEO|ODISSEIA|HISTORIA|HISTORY|DOCUMENTARY|DOCUMENTARIES|DOCU|WILD|ANIMAL PLANET)\b|^RAI STORIA$'),
    ('Notícias', r'\b(?:NEWS|NOTICIAS|EURONEWS|CNN|CNBC|BLOOMBERG|ALJAZEERA|AL JAZEERA|CMTV|TAGESSCHAU24)\b|^RTP\s*3$|^FRANCE (?:24|INFO)\b|^TVE 24$|^RUSSIA TODAY$|^ARTV$|^MOSAICO INFO$'),
    ('Música', r'\b(?:MUSIC|MUSICA|MTV|MEZZO|MCM|STINGRAY|VH1|ICONCERTS|DJAZZ)\b|^TRACE\b'),
    ('Estilo de vida', r'\b(?:KITCHEN|COZINHA|FASHION|HGTV|TRAVELXP|TLC)\b|HOME & GARDEN'),
    ('Religião', r'\b(?:CANCAO NOVA|NOVO TEMPO|KURIAKOS|DAYSTAR|MAANAIM|UNIFE)\b|^TV VERDADE$'),
    ('Séries e entretenimento', r'\b(?:AXN|AMC|SYFY|DIZI|GAMETOON)\b|^STAR (?:CHANNEL|COMEDY|CRIME|FAMILY|LIFE)\b|^SIC (?:CARAS|MULHER|RADICAL|NOVELAS)$|^TVI REALITY$|^RTP MEMORIA$|^E!'),
    ('Generalistas', r'^(?:RTP\s*[12]|RTP (?:ACORES|MADEIRA|AFRICA|INTERNACIONAL)|SIC|TVI|V\+ TVI|PORTO CANAL|GLOBO|RECORD EUROPA|ARD|ZDF|3SAT|ARTE|FRANCE [2345]|RAI [123]|RAI ITALIA|TV5 MONDE|TVEI|AZORES TV|LOCALVISAO TV|CONTA LA)$'),
]
GROUP_RULES = [
    ('Adultos', r'\b(?:ADULT\w*|XXX)\b|18\s*\+'),
    ('Desporto', r'\b(?:DESPORT\w*|SPORT\w*|DEPORT\w*|DAZN|FOOTBALL|FUTEBOL|FUTBOL|NBA|NFL|NHL)\b'),
    ('Infantis', r'\b(?:INFANT\w*|CRIAN\w*|KIDS|CHILDREN|CARTOON)\b'),
    ('Filmes', r'\b(?:FILM\w*|MOVIES?|CINEMA|CINE)\b'),
    ('Notícias', r'\b(?:NOTICI\w*|NEWS|INFORMAC\w*)\b'),
    ('Documentários', r'\b(?:DOCUMENT\w*|DOKU\w*|NATURE|DISCOVERY)\b'),
    ('Música', r'\b(?:MUSIC\w*|MUSIK)\b'),
    ('Estilo de vida', r'\b(?:LIFESTYLE|COZINHA|CULINARIA|TRAVEL|VIAGENS)\b'),
    ('Religião', r'\b(?:RELIG\w*|FAITH|CHRISTIAN)\b'),
    ('Séries e entretenimento', r'\b(?:SERIES|ENTERTAINMENT|ENTRETEN\w*|COMEDY|NOVELAS)\b'),
    ('Generalistas', r'\b(?:GENERALISTAS|GENERAL|REGIONAL\w*)\b'),
]
NAME_RULES = [(category, re.compile(pattern)) for category, pattern in NAME_RULES]
GROUP_RULES = [(category, re.compile(pattern)) for category, pattern in GROUP_RULES]


def category_hint(name, groups):
    """Arguments already normalized by the catalog (case, accents, superscripts)."""
    name = re.sub(r'^(?:(?:[A-Z0-9 &+]{1,18})\s*[:|]\s*)+', '', name)
    name = re.sub(r'\b(?:8K|4K|UHD|FHD|FULL\s*HD|HD|SD|RAW|1080[PI]?|720P|2160P)\b', '', name)
    name = re.sub(r'\s+', ' ', name).strip(' -|:◉')
    if GROUP_RULES[0][1].search(groups):
        return 'Adultos', 3
    for category, pattern in NAME_RULES:
        if pattern.search(name):
            return category, 2
    for category, pattern in GROUP_RULES:
        if pattern.search(groups):
            return category, 1
    return 'Outros', 0


def category_for(name, groups):
    return category_hint(name, groups)[0]
