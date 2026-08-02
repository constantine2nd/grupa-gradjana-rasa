# -*- coding: utf-8 -*-
"""Odseca deo parcele uz medju sa susedom i pravi KML sa oba dela.

    python3 alat/podeli.py 3096/1 --uz 3097 --ostaje 2500
    python3 alat/podeli.py 3096/1 --uz 3097 --ostaje 2500 --rez uzduz

Racuna gde treba da prodje nova medja da bi ostatak imao tacno zadatu povrsinu,
pa upisuje KML u kome se vide tri stvari, svaka svojom bojom i sa povrsinom u
opisu: susedna parcela, ostatak, i deo koji se odvaja.

DVA REZA, oba prava linija -- parcele se dele pravim linijama:

  popreko (podrazumevano)  Popreko na medju, odseca njen kraj. Kad se parcela
                           prema kraju suzava u krak, ovo uzima taj krak.
  uzduz                    Paralelno sa medjom, odseca traku duz cele duzine.
                           Na povijenoj medji daje klin, ne traku iste sirine.

Povrsine se racunaju iz geometrije. Katastarska upisana povrsina je za nijansu
druga (kod 3096/1 je 3.091 prema 3.088,8 m² geometrijski), pa se "--ostaje 2500"
uzima kao 2500 m² GEOMETRIJSKI. To je stroze: po upisanoj meri ostatak ispada
nesto vise, nikad manje.

VAZNO: ovo je racunska podloga za dogovor, ne geodetski elaborat. Deobu parcele
premerava i upisuje ovlasceni geodeta, i konacne cifre su njegove.
"""
import json, math, os, sys

from kml import prstenovi, kml_prsten, LINIJA, POPUNA

HERE = os.path.dirname(os.path.abspath(__file__))


def ucitaj(G, broj):
    r = prstenovi(G[broj]['geom_wkt'])[0][0]
    p = [tuple(map(float, q.strip().split())) for q in r.split(',') if q.strip()]
    return p if p[0] == p[-1] else p + [p[0]]


def povrsina(p):
    return abs(sum(p[i][0] * p[i + 1][1] - p[i + 1][0] * p[i][1]
                   for i in range(len(p) - 1))) / 2


def zajednicka_medja(a, b):
    sb = {(round(x, 2), round(y, 2)) for x, y in b}
    return [(x, y) for x, y in a[:-1] if (round(x, 2), round(y, 2)) in sb]


def odseci(p, n, t):
    """Sutherland-Hodgman: deo poligona p za koji je dot(tacka, n) <= t."""
    out = []
    m = p[:-1] if p[0] == p[-1] else p[:]
    for i in range(len(m)):
        a, b = m[i], m[(i + 1) % len(m)]
        sa = a[0] * n[0] + a[1] * n[1] - t
        sb = b[0] * n[0] + b[1] * n[1] - t
        if sa <= 0:
            out.append(a)
        if (sa < 0 < sb) or (sb < 0 < sa):
            k = sa / (sa - sb)
            out.append((a[0] + k * (b[0] - a[0]), a[1] + k * (b[1] - a[1])))
    return out + [out[0]] if out else []


def po_meri(parcela, smer, cilj):
    """Trazi rez okomit na `smer` tako da odsecen deo ima povrsinu `cilj`.

    Vraca (odseceno, ostatak, t). Odseceno je na strani u koju `smer` pokazuje.
    """
    n = (-smer[0], -smer[1])                     # odsecak je gde je dot(p, smer) veliko
    s = [x * n[0] + y * n[1] for x, y in parcela[:-1]]
    lo, hi = min(s), max(s)
    for _ in range(200):
        t = (lo + hi) / 2
        # oblast dot(p, n) <= t raste sa t, pa premala povrsina znaci: pomeri t navise
        if povrsina(odseci(parcela, n, t)) < cilj:
            lo = t
        else:
            hi = t
    t = (lo + hi) / 2
    return odseci(parcela, n, t), odseci(parcela, smer, -t), t


def podeli(parcela, sused, cilj_ostatka, rez='popreko'):
    medja = zajednicka_medja(parcela, sused)
    if len(medja) < 2:
        sys.exit('parcele nemaju zajednicku medju')

    (x0, y0), (x1, y1) = medja[0], medja[-1]
    d = math.hypot(x1 - x0, y1 - y0)
    u = ((x1 - x0) / d, (y1 - y0) / d)            # duz medje
    n = (-u[1], u[0])                             # popreko na medju

    ukupno = povrsina(parcela)
    cilj = ukupno - cilj_ostatka
    if cilj <= 0:
        sys.exit(f'parcela ima {ukupno:.0f} m², nema sta da se odvoji do {cilj_ostatka:.0f}')

    if rez == 'uzduz':
        # normala mora da gleda U parcelu, dalje od suseda
        cx = sum(x for x, _ in parcela[:-1]) / (len(parcela) - 1)
        cy = sum(y for _, y in parcela[:-1]) / (len(parcela) - 1)
        smer = n if (cx * n[0] + cy * n[1]) < (x0 * n[0] + y0 * n[1]) else (-n[0], -n[1])
        odseceno, ostatak, _ = po_meri(parcela, smer, cilj)
        return odseceno, ostatak, u, n, medja

    # popreko: uzima se onaj kraj medje na kome je parcela uza -- tamo je krak
    def sirina_kod(kraj):
        s0 = kraj[0] * u[0] + kraj[1] * u[1]
        blizu = [abs(-(x - kraj[0]) * u[1] + (y - kraj[1]) * u[0])
                 for x, y in parcela[:-1]
                 if abs((x * u[0] + y * u[1]) - s0) < 25]
        return max(blizu) if blizu else 0.0

    zapad, istok = sirina_kod(medja[0]), sirina_kod(medja[-1])
    smer = u if istok <= zapad else (-u[0], -u[1])
    odseceno, ostatak, _ = po_meri(parcela, smer, cilj)
    return odseceno, ostatak, u, n, medja


def placemark(ime, prsten, opis, stil):
    koord = kml_prsten(','.join(f'{x} {y}' for x, y in prsten))
    return (f'  <Placemark>\n'
            f'    <name>{ime}</name>\n'
            f'    <description>{opis}</description>\n'
            f'    <styleUrl>#{stil}</styleUrl>\n'
            f'    <Polygon><tessellate>1</tessellate><outerBoundaryIs><LinearRing>'
            f'<coordinates>{koord}</coordinates></LinearRing></outerBoundaryIs></Polygon>\n'
            f'  </Placemark>')


if __name__ == '__main__':
    os.chdir(HERE)
    a = sys.argv[1:]
    if not a or '--uz' not in a:
        sys.exit(__doc__)
    broj = a[0]
    sused = a[a.index('--uz') + 1]
    cilj = float(a[a.index('--ostaje') + 1]) if '--ostaje' in a else 2500.0
    rez = a[a.index('--rez') + 1] if '--rez' in a else 'popreko'
    dest = a[a.index('-o') + 1] if '-o' in a else '_izlaz/podela.kml'

    G = json.load(open('geoms.json', encoding='utf-8'))
    for b in (broj, sused):
        if b not in G:
            sys.exit(f'nema parcele {b} u geoms.json')

    P, S = ucitaj(G, broj), ucitaj(G, sused)
    odseceno, ostatak, u, n, medja = podeli(P, S, cilj, rez)
    po, pt, uk = povrsina(ostatak), povrsina(odseceno), povrsina(P)

    # koliko odseceni deo dodiruje medju sa susedom
    duz_medje = 0.0
    for i in range(len(odseceno) - 1):
        a1, b1 = odseceno[i], odseceno[i + 1]
        if all(min(abs(p[0] - m[0]) + abs(p[1] - m[1]) for m in medja) < 0.05
               for p in (a1, b1)):
            duz_medje += math.dist(a1, b1)

    print(f'parcela {broj}: {uk:.1f} m² geometrijski, {G[broj]["povrsina"]} upisano')
    print(f'  rez: {rez} na medju sa {sused}')
    print(f'  ostaje      {po:8.1f} m²   (trazeno {cilj:.0f})')
    print(f'  odvaja se   {pt:8.1f} m²')
    print(f'  zbir        {po + pt:8.1f} m²   (odstupanje od celine {abs(po + pt - uk):.4f})')
    print(f'  po upisanoj meri ostatak je oko {po * G[broj]["povrsina"] / uk:.0f} m²')
    print(f'  {sused} bi sa {G[sused]["povrsina"]} m² preslo na oko '
          f'{G[sused]["povrsina"] + pt * G[broj]["povrsina"] / uk:.0f} m²')

    STIL = {'sused': (LINIJA, POPUNA),
            'ostatak': ('ff3c8c2f', '553c8c2f'),      # zeleno: ostaje
            'odvaja': ('ff1f45a8', '881f45a8')}       # crveno: odvaja se
    stilovi = '\n'.join(
        f'  <Style id="{k}"><LineStyle><color>{l}</color><width>3</width></LineStyle>'
        f'<PolyStyle><color>{f}</color></PolyStyle></Style>' for k, (l, f) in STIL.items())

    telo = '\n'.join([
        placemark(f'Parcela {sused}', S[:-1],
                  f'{G[sused]["povrsina"]} m² · susedna parcela', 'sused'),
        placemark(f'{broj} — ostaje', ostatak[:-1],
                  f'{po:.0f} m² od {uk:.0f} m²', 'ostatak'),
        placemark(f'{broj} — odvaja se', odseceno[:-1],
                  f'{pt:.0f} m² · pripaja se parceli {sused}', 'odvaja'),
    ])

    doc = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
  <name>Podela parcele {broj} — Raša</name>
  <description>Ostaje {po:.0f} m², odvaja se {pt:.0f} m² i pripaja parceli {sused}.
Računska podloga za dogovor, ne geodetski elaborat.</description>
{stilovi}
{telo}
</Document>
</kml>
'''
    os.makedirs(os.path.dirname(dest) or '.', exist_ok=True)
    open(dest, 'w', encoding='utf-8').write(doc)
    print(f'\n{os.path.abspath(dest)}  ({len(doc)} B)')
