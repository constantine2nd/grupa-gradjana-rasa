# -*- coding: utf-8 -*-
"""Pravi samostalnu HTML stranicu od fragmenta koji generise gen.py.

gen.py pravi FRAGMENT -- bez <!doctype>, <html>, <head> i <body> -- jer ga
Artifact platforma sama uvija u te tagove. Za bilo koje drugo objavljivanje
(sopstveni sajt, slanje fajla, otvaranje sa diska) fragment treba uviti sam,
inace nema <meta charset> pa se sa file:// mogu pokvariti š, ć, č, ž i đ.

    python3 standalone.py [izvor] [odrediste] [naslov]

Bez argumenata radi ../katastarski-plan.html -> ../katastarski-plan-web.html.
Treci argument menja <title> i og:title, a ne dira sadrzaj stranice.
"""
import re, sys, os

_os_dir = os.path.dirname(os.path.abspath(__file__)) or '.'
os.chdir(_os_dir)

SRC = sys.argv[1] if len(sys.argv) > 1 else '../katastarski-plan.html'
DST = sys.argv[2] if len(sys.argv) > 2 else '../katastarski-plan-web.html'
NASLOV = sys.argv[3] if len(sys.argv) > 3 else None
OPIS = ('Katastarski plan parcela i puta 7810/2 u Raši, KO Sremski Karlovci. '
        'Podaci iz digitalnog katastarskog plana Republičkog geodetskog zavoda.')

# Stranica se ne provlaci kroz Jekyll (nema front matter), pa `relative_url`
# ovde ne postoji i baseurl se ne sme upisati rukom. Sve putanje su RELATIVNE:
# stranica stoji u korenu sajta, pored manifest.webmanifest, sw.js i assets/,
# pa isto vaze i kad se sajt servira i kad se fajl otvori sa diska.
#
# Bez ovoga plan je bio jedina stranica koja ne registruje service worker --
# ko dobije link bas na njega i otvori ga prvi put, ne dobije nista kesirano.
# A plan je jedina stranica koju neko stvarno otvara u ataru, bez signala.
#
# Trake "nova verzija" ovde nema namerno: nosila bi svoj markup i svoj CSS u
# stranicu koja je inace samostalna. Sadrzaj je i tako mreza-pa-kes, pa je uvek
# svez dok ima signala; nova verzija preuzme kad se zatvore sve kartice.
PWA = '''<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="assets/icons/favicon.svg" type="image/svg+xml">
<link rel="icon" href="assets/icons/favicon.ico" sizes="32x32">
<link rel="apple-touch-icon" href="assets/icons/apple-touch-icon.png">
<meta name="apple-mobile-web-app-title" content="Raša">'''

# Bez ovoga je stranica slepa ulica: samostalan dokument bez ijedne veze ka
# sajtu. Navbar sajta se ovde ne moze pozvati -- trazio bi Bootstrap i celu
# temu, a ovaj dokument stoji sam. Umesto toga dve tanke veze, gore i dole,
# u istoj tipografiji i istim promenljivima koje fragment vec definise.
#
# Putanja je relativna i pokazuje na index.html, ne na "./" -- tako radi i kad
# se sajt servira i kad se fajl otvori sa diska, gde bi "./" dao spisak fajlova.
#
# TEKST JE ODMAH LATINICOM: translit.py se pokrece PRE standalone.py, pa ovo
# kroz njega ne prolazi.
NAZAD_STIL = '''
.nazad-traka,.nazad-dno{max-width:1060px;margin:0 auto;
  padding-left:clamp(18px,4vw,32px);padding-right:clamp(18px,4vw,32px);}
.nazad-traka{padding-top:clamp(20px,4vw,30px);}
.nazad-dno{padding-bottom:clamp(36px,6vw,64px);margin-top:-40px;}
/* Ivica ide na unutrasnji element da bi stala tacno uz sadrzaj, kao linija
   iznad "O planu" -- na spoljnom bi se protegla i preko bocnog paddinga. */
.nazad-crta{border-top:1px solid var(--rule);padding-top:18px;}
.nazad{display:inline-block;font-family:var(--mono);font-size:12.5px;
  letter-spacing:.02em;color:var(--muted);text-decoration:none;}
.nazad:hover,.nazad:focus{color:var(--ink);}
.nazad:focus-visible{outline:2px solid var(--onroad);outline-offset:3px;}
'''

NAZAD_VRH = ('<nav class="nazad-traka">'
             '<a class="nazad" href="index.html">&larr; Grupa građana Raša</a>'
             '</nav>')

NAZAD_DNO = ('<footer class="nazad-dno"><div class="nazad-crta">'
             '<a class="nazad" href="index.html">&larr; Nazad na početnu stranicu</a>'
             '</div></footer>')

REGISTRACIJA = '''<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function () {
    navigator.serviceWorker.register('sw.js', { scope: './' })
      .catch(function (e) { console.warn('Service worker nije registrovan:', e); });
  });
}
</script>'''

frag = open(SRC, encoding='utf-8').read()

m = re.search(r'<title>(.*?)</title>\s*', frag, re.S)
naslov = NASLOV or (m.group(1).strip() if m else 'Katastarski plan')
if m:
    frag = frag[:m.start()] + frag[m.end():]

html = f'''<!doctype html>
<html lang="sr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{naslov}</title>
<meta name="description" content="{OPIS}">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#e9ebe4" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#121511" media="(prefers-color-scheme: dark)">
<meta property="og:type" content="website">
<meta property="og:title" content="{naslov}">
<meta property="og:description" content="{OPIS}">
{PWA}
<style>*,*::before,*::after{{box-sizing:border-box}}body{{margin:0}}{NAZAD_STIL}</style>
</head>
<body>
{NAZAD_VRH}
{frag.strip()}
{NAZAD_DNO}
{REGISTRACIJA}
</body>
</html>
'''

open(DST, 'w', encoding='utf-8').write(html)

# Broje se samo resursi koji se STVARNO povlace pri prikazu: src=, <link href=,
# url() u CSS-u i @import. Obicno <a href> se ne racuna -- link ka mapama nista
# ne ucitava dok se ne klikne, a stranica bez interneta i dalje radi cela.
# Ranije je ovde stajalo prosto brojanje "https?://", pa je adresa Gugl mapa u
# skripti izgledala kao spoljna zavisnost, sto nije.
resursi = (re.findall(r'\bsrc\s*=\s*["\']https?://', html)
           + re.findall(r'<link\b[^>]*\bhref\s*=\s*["\']https?://', html)
           + re.findall(r'url\(\s*["\']?https?://', html)
           + re.findall(r'@import\s+["\']?https?://', html))
odlazni = len(re.findall(r'<a\b[^>]*\bhref\s*=\s*["\']https?://', html))

print(f'{os.path.abspath(DST)}  ({len(html)} B)')
print(f'  naslov: {naslov}')
print(f'  spoljnih zahteva pri prikazu: {len(resursi)}  (0 = radi bez interneta)')
print(f'  odlaznih linkova: {odlazni}  (ne ucitavaju se, otvaraju se na klik)')
