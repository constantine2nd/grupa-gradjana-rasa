#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pravi ikone aplikacije iz geometrije puta 7810/2.

    python3 bin/napravi-ikone.py

Znak je stvarni oblik puta iz alat/put.json, isti onaj koji je predmet
inicijative -- belo na tirkiznoj ($primary iz SCSS-a). Sve ide u assets/icons/.

Zasto potez 30: tanji od toga nestane na 48 px, deblji se slije u mrlju i put
prestane da lici na put. Provereno renderovanjem na 192, 96 i 48.

Maskable varijanta ima vecu marginu. Android ume da isece ikonu u krug, kvadrat
ili kapljicu; garantovano se vidi samo centralnih 80% precnika, pa sadrzaj mora
da stane unutra. Obicna varijanta koristi manju marginu da znak ne bude sitan.

Zavisnosti: cairosvg, Pillow.
"""
import json, os, re, io, sys

import cairosvg
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(HERE)

OUT = 'assets/icons'
TEAL = '#0085A1'          # $primary iz assets/vendor/.../variables/_colors.scss
STROKE = 30               # u koordinatama viewBox-a 512
ROAD = '7810/2'


def road_path(pad_frac):
    """Put upisan u kvadrat 512x512, sa zadatom marginom."""
    wkt = json.load(open('alat/put.json', encoding='utf-8'))[ROAD]['geom_wkt']
    rings = []
    for ring in re.findall(r'\(([-\d\.\s,]+)\)', wkt):
        pts = [tuple(map(float, p.strip().split())) for p in ring.split(',') if p.strip()]
        if len(pts) > 2:
            rings.append(pts)
    allp = [p for r in rings for p in r]
    xs = [p[0] for p in allp]
    ys = [p[1] for p in allp]
    x0, y0 = min(xs), min(ys)
    w, h = max(xs) - x0, max(ys) - y0
    pad = 512 * pad_frac
    box = 512 - 2 * pad
    sc = box / max(w, h)
    ox = pad + (box - w * sc) / 2
    oy = pad + (box - h * sc) / 2
    # y se okrece: katastar raste na gore, SVG na dole
    return ''.join(
        'M' + 'L'.join(f'{ox+(x-x0)*sc:.1f} {512-oy-(y-y0)*sc:.1f}' for x, y in r) + 'Z'
        for r in rings)


def svg(pad_frac):
    d = road_path(pad_frac)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">'
            f'<rect width="512" height="512" fill="{TEAL}"/>'
            f'<path d="{d}" fill="#fff" stroke="#fff" stroke-width="{STROKE}"'
            f' stroke-linejoin="round" stroke-linecap="round"/></svg>').encode()


def png(src, size, dest):
    cairosvg.svg2png(bytestring=src, output_width=size, output_height=size,
                     write_to=os.path.join(OUT, dest))
    print(f'  {dest:28s} {size}x{size}')


os.makedirs(OUT, exist_ok=True)
normal = svg(0.16)
maskable = svg(0.30)

open(os.path.join(OUT, 'favicon.svg'), 'wb').write(normal)
print(f'  {"favicon.svg":28s} vektor')

png(normal, 192, 'icon-192.png')
png(normal, 512, 'icon-512.png')
png(maskable, 192, 'icon-maskable-192.png')
png(maskable, 512, 'icon-maskable-512.png')
# iOS sam zaobljava i ne podnosi providnost -- podloga je puna, pa je u redu
png(normal, 180, 'apple-touch-icon.png')
png(normal, 32, 'favicon-32.png')
png(normal, 16, 'favicon-16.png')

ico = os.path.join(OUT, 'favicon.ico')
Image.open(os.path.join(OUT, 'favicon-32.png')).save(
    ico, sizes=[(16, 16), (32, 32), (48, 48)])
print(f'  {"favicon.ico":28s} 16/32/48')

total = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
print(f'\n{len(os.listdir(OUT))} fajlova, {total/1024:.1f} KB ukupno -> {OUT}/')
