#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prevodi slike iz img/ u WebP.

    python3 bin/smanji-slike.py            # samo izvestaj, nista ne dira
    python3 bin/smanji-slike.py --uradi    # pravi .webp pored originala

Sajt je nosio 11 MB slika, od cega jedan JPEG od 2,5 MB i jedan PNG fotografije
od 3,8 MB. To je bilo skupo i pre PWA; sa service workerom koji ih kesira postaje
neodrzivo.

WebP, ne JPEG: podrzan je svuda od 2020, a na istom kvalitetu daje osetno manje
fajlove. Jedan format znaci da nema <picture> ni image-set() -- pozadine se u
sablonima zadaju kao obican CSS url(), pa bi pregovaranje o formatu tu bilo
mucno.

Pozadine zadrzavaju dimenzije (idu preko cele sirine ekrana). Slike u telu
objave se obaraju na 1600 px po duzoj strani -- prikazuju se u koloni od oko
800 px, pa je i to vec sa rezervom za retina ekrane.
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(HERE)

KVALITET = 80
MAX_STRANICA = 1600      # samo za slike u telu objave

# pozadine idu preko cele sirine, njima se dimenzije ne diraju
POZADINE = {'img/bg-about.jpg', 'img/bg-contact.jpg', 'img/bg-index.jpg',
            'img/bg-post.jpg', 'img/posts/01.png'}

uradi = '--uradi' in sys.argv
ukupno_pre = ukupno_posle = 0
redovi = []

for koren, _, fajlovi in os.walk('img'):
    for ime in sorted(fajlovi):
        if not ime.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue
        put = os.path.join(koren, ime).replace(os.sep, '/')
        cilj = os.path.splitext(put)[0] + '.webp'
        im = Image.open(put)
        w, h = im.size
        if put not in POZADINE and max(w, h) > MAX_STRANICA:
            r = MAX_STRANICA / max(w, h)
            im = im.resize((round(w * r), round(h * r)), Image.LANCZOS)
        im = im.convert('RGB')
        if uradi:
            im.save(cilj, 'WEBP', quality=KVALITET, method=6)
            posle = os.path.getsize(cilj)
        else:
            import io
            b = io.BytesIO()
            im.save(b, 'WEBP', quality=KVALITET, method=6)
            posle = b.tell()
        pre = os.path.getsize(put)
        ukupno_pre += pre
        ukupno_posle += posle
        redovi.append((put, w, h, im.size[0], im.size[1], pre, posle))

for put, w, h, nw, nh, pre, posle in redovi:
    dim = f'{w}x{h}' + (f' -> {nw}x{nh}' if (w, h) != (nw, nh) else '')
    print(f'  {put:24s} {dim:22s} {pre/1024:8.0f} KB -> {posle/1024:7.0f} KB'
          f'   -{100*(1-posle/pre):.0f}%')

print(f'\n  {"UKUPNO":24s} {"":22s} {ukupno_pre/1024:8.0f} KB -> {ukupno_posle/1024:7.0f} KB'
      f'   -{100*(1-ukupno_posle/ukupno_pre):.0f}%')
if not uradi:
    print('\n(probni prolaz -- pokrenuti sa --uradi da se fajlovi zaista naprave)')
