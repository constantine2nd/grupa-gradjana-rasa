# -*- coding: utf-8 -*-
"""Gradi provera-parcela.html iz geoms.json + spiska potpisnika u build.py.

Parcele se razvrstavaju po RASTOJANJU DO PUTA 7810/2 (put.json), jer je put ono
oko cega inicijativa stoji. Rastojanje je od temena parcele do najblize duzi
poligona puta, u metrima (geometrija je u EPSG:32634, UTM 34N).

    python3 build.py && python3 gen.py && python3 translit.py ../provera-parcela.html

Tekst u sekciji "Nalazi" u page.tmpl.html pisan je rucno -- procitati ga posle
svake izmene spiska.
"""
import json, math, html, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
# Interna verzija ide u _izlaz/, koji se ne komituje -- sadrzi imena.
# Javna je fragment koji standalone.py uvija i smesta u koren sajta.
os.makedirs(os.path.join(HERE, '_izlaz'), exist_ok=True)
OUT = os.path.join(HERE, '_izlaz', 'provera-parcela.html')
OUT_PUB = os.path.join(HERE, '_izlaz', 'katastarski-plan.html')
DATUM = '31.07.2026.'

# ucitava OWNERS, G (geometrije), UNIQUE, SIGN_SET iz build.py
exec(open('build.py', encoding='utf-8').read().split('# ---- clusters')[0])

ON_ROAD = 5      # m, do ovoga se racuna da parcela izlazi na put
BEHIND = 300     # m, do ovoga je zaledje uz trasu; preko toga je van trase

sig = [p for p in UNIQUE if p in G]

# ---------- put ----------
ROAD = {}
for k, v in json.load(open('put.json', encoding='utf-8')).items():
    ROAD[k] = {'rings': rings(v['geom_wkt']), 'povrsina': v['povrsina']}
MAIN = '7810/2'
segs = []
for r in ROAD[MAIN]['rings']:
    segs += list(zip(r, r[1:]))


def _seg_dist(p, a, b):
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def dist_to_road(p):
    return min(_seg_dist(v, a, b) for v in G[p]['rings'][0] for a, b in segs)


GRP, DIST = {}, {}
for p in sig:
    d = dist_to_road(p)
    DIST[p] = round(d)
    GRP[p] = 'onroad' if d <= ON_ROAD else ('behind' if d <= BEHIND else 'off')

ONROAD = [p for p in sig if GRP[p] == 'onroad']
BEHINDL = [p for p in sig if GRP[p] == 'behind']
OFF = [p for p in sig if GRP[p] == 'off']

# ---------- crtanje ----------
xs = [G[p]['c'][0] for p in sig]
ys = [G[p]['c'][1] for p in sig]
M = 170
x0, x1 = min(xs) - M, max(xs) + M
y0, y1 = min(ys) - M, max(ys) + M
W, H = x1 - x0, y1 - y0

context = [k for k, v in G.items()
           if x0 - 40 <= v['c'][0] <= x1 + 40 and y0 - 40 <= v['c'][1] <= y1 + 40
           and k not in SIGN_SET]


def path(rs):
    out = []
    for pts in rs:
        d = [('M' if i == 0 else 'L') + f'{x-x0:.1f} {y1-y:.1f}'
             for i, (x, y) in enumerate(pts)]
        out.append(''.join(d) + 'Z')
    return ''.join(out)


def view(ps, pad=90):
    ax, ay = [], []
    for p in ps:
        for r in G[p]['rings']:
            for (x, y) in r:
                ax.append(x - x0); ay.append(y1 - y)
    a, b = min(ax) - pad, min(ay) - pad
    w, h = max(ax) + pad - a, max(ay) + pad - b
    ar = W / H
    if w / h > ar:
        nh = w / ar; b -= (nh - h) / 2; h = nh
    else:
        nw = h * ar; a -= (nw - w) / 2; w = nw
    return [round(a, 1), round(b, 1), round(w, 1), round(h, 1)]


ctx = ''.join(f'<path d="{path(G[k]["rings"])}"/>' for k in context)
rd = ''.join(f'<path d="{path(v["rings"])}"><title>Пут {k} · {v["povrsina"]} m²</title></path>'
             for k, v in sorted(ROAD.items()))
sg = ''.join(f'<path class="s {GRP[p]}" d="{path(G[p]["rings"])}">'
             f'<title>Парцела {p} · {G[p]["povrsina"]} m² · {DIST[p]} m до пута</title></path>'
             for p in sig)
lb = ''.join(f'<text x="{G[p]["c"][0]-x0:.0f}" y="{y1-G[p]["c"][1]:.0f}">{p}</text>'
             for p in sig)

# ---------- tabela ----------
GRPLABEL = {'onroad': 'уз пут', 'behind': 'залеђе', 'off': 'ван трасе'}
MODELABEL = {'asfalt': 'асфалт', 'internet': 'интернет', 'oba': 'асфалт + интернет'}

dupes = {}
for o, ps, mode in OWNERS:
    for p in ps:
        dupes.setdefault(p, []).append(o)
# parcela koju navodi vise potpisnika: ako je suvlasnistvo potvrdjeno iz B lista,
# to nije sukob nego zajednicka svojina
SHARED = globals().get('SUVLASNISTVO', {})
conflicts = sorted(p for p, v in dupes.items() if len(v) > 1 and p not in SHARED)
shared_ok = sorted(p for p, v in dupes.items() if len(v) > 1 and p in SHARED)
nepotpisali = sorted({n for p in SHARED for n in SHARED[p].get('nepotpisali', [])})
missing = [p for p in UNIQUE if p not in G]

CHIP_OK = '<span class="chip ok">уписана</span>'
CHIP_NO = '<span class="chip no">нема је</span>'

try:
    OBJ = json.load(open('objekti.json', encoding='utf-8'))
except FileNotFoundError:
    OBJ = {}

trows = []
for o, ps, mode in OWNERS:
    first = True
    for p in ps:
        d = G.get(p)
        cls = 'bad' if not d else ('warn' if p in conflicts else
                                   ('shared' if p in SHARED else ''))
        area = f'{d["povrsina"]:,}'.replace(',', '.') if d else '—'
        grp = f'<span class="chip {GRP[p]}">{GRPLABEL[GRP[p]]}</span>' if d else ''
        dist = (DIST[p] if DIST[p] > ON_ROAD else '<span class="sub">излази</span>') if d else ''
        ob = OBJ.get(p)
        obj = (f'{ob["m2"]}' + (f' <span class="sub">×{ob["n"]}</span>' if ob["n"] > 1 else '')) \
            if ob else ('<span class="sub">нема</span>' if d else '')
        trows.append(
            f'<tr class="{cls}">'
            f'<td class="own">{html.escape(o) if first else ""}</td>'
            f'<td class="num">{p}'
            + (f'<br><span class="sub">сувл. {SHARED[p]["udeo"]}</span>'
               if p in SHARED else '') + '</td>'
            f'<td class="num r">{area}</td>'
            f'<td class="num r">{obj}</td>'
            f'<td>{CHIP_OK if d else CHIP_NO}</td>'
            f'<td>{grp}</td>'
            f'<td class="num r">{dist}</td>'
            f'<td>{MODELABEL[mode]}</td>'
            f'</tr>')
        first = False

tot = sum(G[p]['povrsina'] for p in sig)
road_len = ROAD[MAIN]['povrsina']

# Statistika: plocice za "ne postoji" i "dvostruka prijava" se prikazuju samo
# ako ima sta da se prijavi. Kad je sve cisto, prva plocica to i kaze.
def tile(n, txt, flag=False):
    return f'    <div class="stat{" flag" if flag else ""}"><b>{n}</b><span>{txt}</span></div>'


clean = not missing and not conflicts
tiles = [tile(len(UNIQUE),
              'јединствених парцела, све потврђене у катастру' if clean
              else 'јединствених парцела на списку')]
if not clean:
    tiles.append(tile(len(sig), 'потврђено у катастру'))
    if missing:
        tiles.append(tile(len(missing), 'не постоји под тим бројем', True))
    if conflicts:
        tiles.append(tile(len(conflicts), 'нераспетљана двострука пријава', True))
if nepotpisali:
    tiles.append(tile(len(nepotpisali), 'уписана сувласника без потписа', True))
if OFF:
    tiles.append(tile(len(OFF), 'не излази на пут 7810/2', True))
tiles.append(tile(f'{tot/10000:.2f}'.replace('.', ','),
                  f'хектара укупно ({tot:,} m²)'.replace(',', '.')))

REPL = {
    '%%TILES%%': '\n'.join(tiles),
    '%%CTX%%': ctx, '%%SIG%%': sg, '%%LBL%%': lb, '%%ROAD%%': rd,
    '%%W%%': f'{W:.0f}', '%%H%%': f'{H:.0f}', '%%NCTX%%': str(len(context)),
    '%%VALL%%': json.dumps([0, 0, round(W, 1), round(H, 1)]),
    '%%VONROAD%%': json.dumps(view(ONROAD)),
    '%%VOFF%%': json.dumps(view(OFF)) if OFF else json.dumps([0, 0, W, H]),
    '%%TBODY%%': ''.join(trows),
    '%%TOTHA%%': f'{tot/10000:.2f}'.replace('.', ','),
    '%%TOTM2%%': f'{tot:,}'.replace(',', '.'),
    '%%NTOTAL%%': str(len(UNIQUE)), '%%NOK%%': str(len(sig)),
    '%%NMISS%%': str(len(missing)), '%%NDUP%%': str(len(conflicts)),
    '%%NOWNERS%%': str(len(OWNERS)),
    '%%NONROAD%%': str(len(ONROAD)), '%%NBEHIND%%': str(len(BEHINDL)),
    '%%NOFF%%': str(len(OFF)),
    '%%OFFLIST%%': ', '.join(sorted(OFF)),
    '%%MAXBEHIND%%': str(max((DIST[p] for p in BEHINDL), default=0)),
    '%%MINOFF%%': str(min((DIST[p] for p in OFF), default=0)),
    '%%MAXOFF%%': str(max((DIST[p] for p in OFF), default=0)),
    '%%ROADM2%%': f'{road_len:,}'.replace(',', '.'),
    '%%NOBJ%%': str(sum(1 for p in sig if p in OBJ)),
    '%%DATUM%%': DATUM,
    '%%NSHARED%%': str(len(shared_ok)),
    '%%NEPOTPISALI%%': ' и '.join(nepotpisali) or '—',
    '%%NNEPOTPISALI%%': str(len(nepotpisali)),
}

def render(tmpl, dest):
    s = open(tmpl, encoding='utf-8').read()
    for k, v in REPL.items():
        s = s.replace(k, v)
    left = sorted(set(s.split('%%')[1::2]))
    if left:
        print(f'UPOZORENJE ({tmpl}): nezamenjeni tokeni ->', left[:8], file=sys.stderr)
    open(dest, 'w', encoding='utf-8').write(s)
    return s


out = render('page.tmpl.html', OUT)
pub = render('page-javno.tmpl.html', OUT_PUB)

# javna verzija ne sme da sadrzi nijedno ime sa potpisnog spiska
imena = {o for o, _, _ in OWNERS} | {n for p in SHARED for n in SHARED[p].get('svi', [])}
procurelo = sorted(i for i in imena if i in pub)
if procurelo:
    print('GRESKA: imena u javnoj verziji ->', procurelo, file=sys.stderr)
    sys.exit(1)

print(f'{OUT}      ({len(out)} B)')
print(f'{OUT_PUB}  ({len(pub)} B, provereno: bez imena)')
print(f'  parcela na spisku: {len(UNIQUE)}   nadjeno: {len(sig)}   nema: {missing}')
print(f'  sukobi: {conflicts}   suvlasnistvo (uredu): {shared_ok}')
print(f'  upisani suvlasnici koji nisu potpisali: {nepotpisali}')
print(f'  uz put {len(ONROAD)} | zaledje {len(BEHINDL)} (do {REPL["%%MAXBEHIND%%"]} m)'
      f' | van trase {len(OFF)} {sorted(OFF)}')
print(f'  put {MAIN}: {road_len} m²   susedne parcele na planu: {len(context)}')
