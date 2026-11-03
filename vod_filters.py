"""Local VOD facets from catalog labels, never inferred production countries."""
import re

VOD_COUNTRIES = {'EN':'Inglês / Internacional', 'IN':'Índia', 'PK':'Paquistão', 'MT':'Malta',
                 'NORDIC':'Países nórdicos', 'OTHER':'País / idioma não indicado'}
COUNTRY_NAMES = [
 ('PT',r'PORTUG(?:AL|UESE)'),('BR',r'BRA[ZS]IL'),('EN',r'ENGLISH'),
 ('ES',r'ESPANA|SPANISH'),('FR',r'FRANCE|FRENCH'),('DE',r'GERMANY|GERMAN'),
 ('IT',r'ITALY|ITALIAN'),('GR',r'GREECE|GREEK'),('NL',r'NETHERLANDS|DUTCH'),
 ('SE',r'SVENSK\w*|SWEDISH'),('DK',r'DANSK|DANISH'),('NO',r'NORSK|NORWEGIAN'),
 ('FI',r'FINNISH|SUOMI'),('PL',r'POLSKA|POLISH'),('IR',r'PERSIAN'),
 ('IN',r'HINDI|INDIAN|TAMIL|TELUGU|MALAYALAM|KANNADA'),('PK',r'PAKISTAN'),
 ('TR',r'TURKISH'),('AL',r'ALBANIA'),('RU',r'RUSSIAN|RUSSAIN'),
 ('PH',r'PHILIPPINES'),('MT',r'MALTA'),('CA',r'QUEBEC'),('ARAB',r'ARABIC'),
 ('NORDIC',r'NORDIC'),('ASIA',r'ASIA')]
COUNTRY_NAMES = [(c,re.compile(r'^(?:'+p+r')\b')) for c,p in COUNTRY_NAMES]
GENRES = [
 ('Ação',r'ACAO|ACCION|ACTION|AKTION|ΔΡΑΣΗ'),
 ('Aventura',r'AVENTURA|ADVENTURE|AVENTURE|ABENTEUER|ΠΕΡΙΠΕΤΕΙΑ'),
 ('Animação',r'ANIMACAO|ANIMACION|ANIMATION|ANIME|ANIMAZIONE|ΚΙΝΟΥΜΕΝΑ'),
 ('Comédia',r'COMEDIA|COMEDY|COMEDIE|KOMODIE|ΚΩΜΩΔΙΑ'),
 ('Drama',r'DRAMA|DRAME|ΔΡΑΜΑ'),('Crime',r'CRIME|CRIMEN|KRIMI|ΑΣΤΥΝΟΜΙΚΗ'),
 ('Documentário',r'DOCUMENT\w*|DOCU(?:-SERIES)?|DOKU\w*|ΝΤΟΚΙΜΑΝΤΕΡ'),
 ('Família',r'FAMILIA|FAMILY|FAMILLE|FAMILIEN|ΟΙΚΟΓΕΝΕΙΑΚΗ'),
 ('Infantil',r'INFANT\w*|KIDS|CHILDREN|ENFANTS'),
 ('Fantasia',r'FANTASIA|FANTASY|FANTASTIQUE|ΦΑΝΤΑΣΙΑΣ'),
 ('Ficção científica',r'FICCAO CIENTIFICA|CIENCIA FICCION|SCI[ -]?FI|SCIENCE[ -]FICTION'),
 ('Terror',r'TERROR|HORROR|HORREUR|ΤΡΟΜΟΥ'),
 ('Suspense',r'SUSPENSE|THRILLER|ΘΡΙΛΕΡ'),('Mistério',r'MISTERIO|MYSTERY|MYSTERE|ΜΥΣΤΗΡΙΟΥ'),
 ('Romance',r'ROMANCE|ROMANT\w*|ΑΙΣΘΗΜΑΤΙΚΗ'),
 ('História',r'HISTOR\w*|ΙΣΤΟΡΙΚΗ'),('Guerra',r'GUERRA|WAR|GUERRE|KRIEG|ΠΟΛΕΜΙΚΗ'),
 ('Western',r'WESTERN|FAROESTE'),('Música',r'MUSIC\w*|MUSIK'),
 ('Reality',r'REALITY'),('Talk show',r'TALK(?: SHOW)?'),('Desporto',r'DESPORT\w*|SPORT\w*|SOCCER|FOOTBALL|BASKETBALL|RUGBY|WRESTLING|MMA|UFC'),
 ('Adultos',r'ADULT\w*|XXX')]
GENRES = [(g,re.compile(r'\b(?:'+p+r')\b')) for g,p in GENRES]
UNKNOWN_GENRE = 'Sem género indicado'


def countries_for(item, normalize, known):
    groups = item.get('groups') or [item.get('group','')]
    codes=[]
    # A PT/BR group can contain distinct PT and BR editions of the same title.
    name = re.match(r'^(PT|BR)(?:\s*[-:|]|\s)', normalize(item.get('name','')))
    if name and any(re.match(r'^PT/BR\b',normalize(g)) for g in groups):
        return [name[1]]
    for group in groups:
        value=normalize(group)
        prefix=re.match(r'^([A-Z]{2,6}(?:/[A-Z]{2,6})*)(?=\s|[-|:]|$)',value)
        found=[c for c in prefix[1].split('/') if c in known or c in VOD_COUNTRIES] if prefix else []
        if not found:
            for code,pattern in COUNTRY_NAMES:
                if pattern.search(value):
                    found=[code];break
        codes.extend(found)
    return list(dict.fromkeys(codes)) or ['OTHER']


def genres_for(item, normalize):
    metadata=normalize(item.get('genre') or '')
    groups=normalize(' '.join(item.get('groups') or [item.get('group','')]))
    # Metadata is strongest; category labels supply a fallback, never the title.
    values=[label for label,pattern in GENRES if pattern.search(metadata)]
    if not values:
        values=[label for label,pattern in GENRES if pattern.search(groups)]
    return values or [UNKNOWN_GENRE]
