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
<style>*,*::before,*::after{{box-sizing:border-box}}body{{margin:0}}</style>
</head>
<body>
{frag.strip()}
</body>
</html>
'''

open(DST, 'w', encoding='utf-8').write(html)
print(f'{os.path.abspath(DST)}  ({len(html)} B)')
print(f'  naslov: {naslov}')
print(f'  spoljnih zahteva: {len(re.findall(r"https?://", html))}  (0 = radi bez interneta)')
