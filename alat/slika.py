# -*- coding: utf-8 -*-
"""Crta PNG sa podelom parcele, za slanje porukom.

    python3 alat/slika.py 3096/1 --uz 3097 --ostaje 2500

Pise u alat/_izlaz/podela.png. Uspravan format 1080x1350, jer se tako otvara na
telefonu bez zumiranja; tekst je cirilicom, brojevi u kvadratnim metrima.

Zasto zasebno od kml.py: KML je za mape i geodetu, ovo je za razgovor. Ovde se
smeju stvari koje u KML-u nemaju sta da traze -- razmernik, strelica za sever,
povrsine ispisane preko parcela.
"""
import json, math, os, sys

from PIL import Image, ImageDraw, ImageFont

from podeli import ucitaj, podeli, povrsina, zajednicka_medja

HERE = os.path.dirname(os.path.abspath(__file__))

W, H = 1080, 1350
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_B = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

PAPIR = (247, 247, 243)
MASTILO = (26, 30, 25)
SIVO = (120, 126, 118)
SUSED = (0, 133, 161)
OSTAJE = (47, 128, 62)
ODVAJA = (196, 62, 32)


def font(v, deb=False):
    return ImageFont.truetype(FONT_B if deb else FONT, v)


def tezisteX(p):
    """Teziste poligona -- za natpis, jer prosek temena beži ka gustim uglovima."""
    m = p[:-1] if p[0] == p[-1] else p
    a = cx = cy = 0.0
    for i in range(len(m)):
        x0, y0 = m[i]
        x1, y1 = m[(i + 1) % len(m)]
        f = x0 * y1 - x1 * y0
        a += f
        cx += (x0 + x1) * f
        cy += (y0 + y1) * f
    a /= 2
    return (cx / (6 * a), cy / (6 * a))


def nacrtaj(broj, sused, cilj, dest):
    os.chdir(HERE)
    G = json.load(open('geoms.json', encoding='utf-8'))
    P, S = ucitaj(G, broj), ucitaj(G, sused)
    ods, ost, u, n, medja = podeli(P, S, cilj)
    po, pt, uk = povrsina(ost), povrsina(ods), povrsina(P)
    up_ost = po * G[broj]['povrsina'] / uk
    up_novi = G[sused]['povrsina'] + pt * G[broj]['povrsina'] / uk

    im = Image.new('RGB', (W, H), PAPIR)
    d = ImageDraw.Draw(im, 'RGBA')

    # --- zaglavlje ---
    d.text((60, 62), 'Предлог поделе', font=font(52, True), fill=MASTILO)
    d.text((60, 128), f'парцеле {broj} и {sused} · Раша', font=font(30), fill=SIVO)
    d.line([(60, 190), (W - 60, 190)], fill=(214, 218, 210), width=2)

    # --- plan ---
    gore, dole = 230, H - 430
    sve = P + S
    ax = min(x for x, _ in sve); bx = max(x for x, _ in sve)
    ay = min(y for _, y in sve); by = max(y for _, y in sve)
    m = 70
    sc = min((W - 2 * m) / (bx - ax), (dole - gore - 2 * m) / (by - ay))
    ox = (W - (bx - ax) * sc) / 2
    oy = gore + (dole - gore - (by - ay) * sc) / 2

    def T(p):
        return (ox + (p[0] - ax) * sc, oy + (by - p[1]) * sc)

    for prsten, boja, alfa, deb in ((S, SUSED, 55, 3), (ost, OSTAJE, 90, 3), (ods, ODVAJA, 150, 3)):
        d.polygon([T(p) for p in prsten], fill=boja + (alfa,), outline=boja)
        d.line([T(p) for p in prsten], fill=boja, width=deb)

    def natpis(prsten, gornji, donji, boja, odmak=0):
        cx, cy = T(tezisteX(prsten))
        if odmak:                       # uzan oblik: natpis iznad, sa vodilicom
            d.line([(cx, cy), (cx, cy + odmak + 30)], fill=boja, width=3)
            d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=boja)
            cy += odmak
        f1, f2 = font(30, True), font(25)
        w1 = d.textbbox((0, 0), gornji, font=f1)[2]
        w2 = d.textbbox((0, 0), donji, font=f2)[2]
        w = max(w1, w2) + 26
        d.rounded_rectangle([cx - w / 2, cy - 40, cx + w / 2, cy + 34], 8,
                            fill=(255, 255, 255, 216))
        d.text((cx - w1 / 2, cy - 34), gornji, font=f1, fill=boja)
        d.text((cx - w2 / 2, cy + 2), donji, font=f2, fill=MASTILO)

    natpis(S, sused, f'{G[sused]["povrsina"]:,} m²'.replace(',', '.'), SUSED)
    natpis(ost, broj, f'{up_ost:,.0f} m²'.replace(',', '.'), OSTAJE)
    natpis(ods, 'прелази', f'{pt:,.0f} m²'.replace(',', '.'), ODVAJA, odmak=-96)

    # --- razmernik i sever ---
    duz = 50 * sc
    yb = dole - 26
    d.line([(60, yb), (60 + duz, yb)], fill=MASTILO, width=4)
    for x in (60, 60 + duz):
        d.line([(x, yb - 9), (x, yb + 9)], fill=MASTILO, width=4)
    d.text((60 + duz + 14, yb - 15), '50 m', font=font(24), fill=MASTILO)
    sx, sy = W - 96, yb - 8
    d.polygon([(sx, sy - 40), (sx - 13, sy), (sx, sy - 11), (sx + 13, sy)], fill=MASTILO)
    d.text((sx - 9, sy + 4), 'С', font=font(24, True), fill=MASTILO)

    # --- objasnjenje ---
    y = dole + 34
    for boja, tekst in (
            (ODVAJA, f'прелази на {sused}: {pt:,.0f} m²'.replace(',', '.')),
            (OSTAJE, f'{broj} остаје: {up_ost:,.0f} m²'.replace(',', '.')),
            (SUSED, f'{sused} сада: {G[sused]["povrsina"]:,} m²'.replace(',', '.'))):
        d.rounded_rectangle([60, y + 5, 88, y + 33], 5, fill=boja + (170,), outline=boja)
        d.text((104, y + 2), tekst, font=font(31), fill=MASTILO)
        y += 52

    y += 18
    d.line([(60, y), (W - 60, y)], fill=(214, 218, 210), width=2)
    y += 22
    d.text((60, y), f'{sused} после припајања: {up_novi:,.0f} m²'.replace(',', '.'),
           font=font(34, True), fill=MASTILO)
    y += 52
    d.text((60, y), f'Услов је био да {broj} не падне испод '
                    f'{cilj:,.0f} m².'.replace(',', '.'), font=font(27), fill=SIVO)
    y += 40
    d.text((60, y), 'Рачунато из дигиталног катастарског плана РГЗ-а.',
           font=font(27), fill=SIVO)
    y += 38
    d.text((60, y), 'Коначну меру даје овлашћени геодета.', font=font(27), fill=SIVO)

    os.makedirs(os.path.dirname(dest) or '.', exist_ok=True)
    im.save(dest, 'PNG')
    return dest, po, pt, up_ost, up_novi


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a or '--uz' not in a:
        sys.exit(__doc__)
    broj = a[0]
    sused = a[a.index('--uz') + 1]
    cilj = float(a[a.index('--ostaje') + 1]) if '--ostaje' in a else 2500.0
    dest = a[a.index('-o') + 1] if '-o' in a else '_izlaz/podela.png'
    p, po, pt, uo, un = nacrtaj(broj, sused, cilj, dest)
    print(os.path.abspath(p))
    print(f'  ostaje {po:.0f} m² geometrijski (~{uo:.0f} upisano), prelazi {pt:.0f} m²')
    print(f'  {sused} posle: ~{un:.0f} m²')
    print(f'  {os.path.getsize(p) / 1024:.0f} KB, {W}x{H}')
