"""Rebuild original, lightweight PNG artwork. Development only: requires Pillow."""
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent / 'public' / 'assets'
OUT.mkdir(exist_ok=True)
INK = '#e5f0f3'
ACCENT = '#e5c28b'
COLORS = dict(tv='#7ad4c5', movie='#e5c28b', series='#b9ace5', all='#efca83',
              country='#8dc8e4', group='#91cbbd', episode='#b9ace5',
              search='#8dc8e4', quality='#7ad4c5', options='#b9ace5', refresh='#7ad4c5')


def icon(name, size=64):
    im = Image.new('RGBA',(256,256))
    class ScaledDraw:
        def __getattr__(self, method):
            def paint(coords, *args, **kwargs):
                def scale(value):
                    return [scale(v) for v in value] if isinstance(value,(tuple,list)) else value*4
                for key in ('width','radius'):
                    if key in kwargs:
                        kwargs[key] *= 4
                return getattr(ImageDraw.Draw(im),method)(scale(coords),*args,**kwargs)
            return paint
    d = ScaledDraw()
    ink = COLORS.get(name, INK)
    def line(points,fill=ink,width=4): d.line(points,fill=fill,width=width)
    def box(bounds): d.rounded_rectangle(bounds,radius=4,outline=ink,width=4)
    if name=='tv':
        box((8,12,56,46));line([(24,53),(40,53)]);line([(32,46),(32,53)])
        d.polygon([(28,22),(28,37),(41,30)],fill=ACCENT)
    elif name=='movie':
        box((9,12,55,52));line([(9,25),(55,25)])
        for x in (14,28,42): line([(x,12),(x+7,24)])
        d.polygon([(27,31),(27,44),(39,37)],fill=ACCENT)
    elif name=='series':
        box((16,22,57,54));line([(12,45),(8,45),(8,14),(49,14)]);line([(16,7),(42,7)])
        d.polygon([(31,30),(31,45),(43,37)],fill=ACCENT)
    elif name=='all':
        d.polygon([(32,7),(39,23),(57,25),(43,38),(47,56),(32,46),(17,56),(21,38),(7,25),(25,23)],fill='#554834',outline=ink,width=4)
    elif name=='country':
        d.ellipse((8,8,56,56),outline=ink,width=4)
        d.ellipse((22,8,42,56),outline=ink,width=3)
        line([(8,32),(56,32)]);line([(13,20),(51,20)],width=3);line([(13,44),(51,44)],width=3)
    elif name=='group':
        d.line([(8,51),(8,16),(26,16),(32,23),(56,23),(56,51),(8,51)],fill=ink,width=4)
        line([(17,32),(46,32)],ACCENT);line([(17,41),(38,41)],ACCENT)
    elif name=='search':
        d.ellipse((10,8,42,40),outline=ink,width=4);line([(38,36),(55,53)],width=5)
    elif name=='quality':
        for x,y in [(14,36),(29,25),(44,13)]:d.rounded_rectangle((x,y,x+9,52),radius=2,fill=ink)
    elif name=='options':
        for y,x in [(16,23),(32,43),(48,19)]:
            line([(8,y),(56,y)]);d.ellipse((x-5,y-5,x+5,y+5),fill='#14242e',outline=ACCENT,width=3)
    elif name=='refresh':
        d.arc((11,11,53,53),35,300,fill=ink,width=4)
        d.polygon([(48,7),(56,24),(38,21)],fill=ACCENT)
    elif name=='episode':
        d.ellipse((8,8,56,56),outline=ink,width=4);d.polygon([(26,20),(26,44),(44,32)],fill=ACCENT)
    return im.resize((size,size),Image.Resampling.LANCZOS)


for name in ('tv','movie','series','all','country','group','search','quality','options','refresh','episode'):
    icon(name).save(OUT/(name+'.png'),optimize=True)

for name in ('tv','movie','series','all','country','group','episode'):
    backgrounds = dict(tv='#173b40', movie='#393229', series='#2c2d46', all='#393429')
    im=Image.new('RGB',(600,240),backgrounds.get(name,'#1b3343'));d=ImageDraw.Draw(im)
    # Quiet architectural lines; no external posters, fonts or stock imagery.
    for x in range(250,700,48):
        d.line([(x,0),(x-120,240)],fill='#203744',width=1)
    d.ellipse((330,-110,650,210),outline='#30434a',width=2)
    d.ellipse((375,-65,605,165),outline='#30434a',width=1)
    d.rectangle((40,44,46,196),fill=COLORS[name])
    mark=icon(name,160)
    im.paste(mark,(76,40),mark)
    d.line([(302,160),(520,160)],fill='#40525a',width=2)
    d.line([(302,177),(448,177)],fill='#40525a',width=2)
    im.save(OUT/('art-'+name+'.png'),optimize=True)

# Media Forge Lab: overlapping media frames and a clear play symbol.
# All coordinates are vector geometry; PNG exports support legacy MAG WebKit.
logo = Image.new('RGBA',(512,512), '#101d29')
d = ImageDraw.Draw(logo)
d.rounded_rectangle((100,116,348,308),radius=28,fill='#183b42',outline='#7ad4c5',width=16)
d.rounded_rectangle((160,184,408,376),radius=28,fill='#152935',outline='#e5f0f3',width=14)
d.polygon([(252,226),(252,334),(338,280)],fill=ACCENT)
for name in ('media-forge-lab.png', 'magforgelab.png'):
    logo.resize((128,128),Image.Resampling.LANCZOS).save(OUT/name,optimize=True)
for size in (192,512):
    logo.resize((size,size),Image.Resampling.LANCZOS).save(OUT.parent/'web'/('icon-%s.png'%size),optimize=True)
logo.resize((128,128),Image.Resampling.LANCZOS).save(OUT.parent/'tv'/'brand.png',optimize=True)
(OUT/'media-forge-lab.svg').write_text('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" role="img" aria-label="Media Forge Lab">
<rect width="512" height="512" rx="100" fill="#101d29"/>
<rect x="108" y="124" width="232" height="176" rx="20" fill="#183b42" stroke="#7ad4c5" stroke-width="16"/>
<rect x="167" y="191" width="234" height="178" rx="21" fill="#152935" stroke="#e5f0f3" stroke-width="14"/>
<path d="M252 226v108l86-54z" fill="#e5c28b"/>
</svg>''', encoding='utf-8')

print('Built',len(list(OUT.glob('*.png'))),'local PNG assets')
