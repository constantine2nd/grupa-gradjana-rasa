# -*- coding: utf-8 -*-
import json, re, math
import os as _os, sys as _sys
_os.chdir(_os.path.dirname(_os.path.abspath(__file__)) or '.')

geoms = json.load(open('geoms.json', encoding='utf-8'))
res = json.load(open('results.json', encoding='utf-8'))

# Spisak potpisnika i suvlasnistva stoji odvojeno, jer sadrzi licne podatke
# i ne ide u javni repozitorijum. Vidi spisak.primer.py.
exec(open('spisak.py', encoding='utf-8').read())

SIGN = []
for o, ps, m in OWNERS:
    for p in ps:
        SIGN.append(p)
SIGN_SET = set(SIGN)
UNIQUE = sorted(SIGN_SET)


def rings(wkt):
    """return list of rings, each a list of (x,y)"""
    out = []
    for chunk in re.findall(r'\(([-\d\.,\s]+)\)', wkt):
        pts = []
        for pair in chunk.split(','):
            a = pair.split()
            if len(a) == 2:
                pts.append((float(a[0]), float(a[1])))
        if len(pts) > 2:
            out.append(pts)
    return out


def centroid(rs):
    pts = rs[0]
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


G = {}
for k, v in geoms.items():
    r = rings(v['geom_wkt'])
    if r:
        G[k] = {'rings': r, 'c': centroid(r), 'povrsina': v['povrsina'],
                'status': v['status_parcele_opis']}

# ---- clusters of signatory parcels (single linkage, 220 m) ----
sig = [p for p in UNIQUE if p in G]
parent = {p: p for p in sig}


def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a


for i, a in enumerate(sig):
    for b in sig[i + 1:]:
        ax, ay = G[a]['c']
        bx, by = G[b]['c']
        if math.hypot(ax - bx, ay - by) < 220:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

groups = {}
for p in sig:
    groups.setdefault(find(p), []).append(p)
groups = sorted(groups.values(), key=lambda g: -sum(G[p]['c'][1] for p in g) / len(g))
gname = {}
labels = ['SEVER', 'CENTAR', 'JUG', 'D', 'E']
for i, g in enumerate(groups):
    for p in g:
        gname[p] = i

# ---- viewport ----
xs = [G[p]['c'][0] for p in sig]
ys = [G[p]['c'][1] for p in sig]
MARGIN = 180
x0, x1 = min(xs) - MARGIN, max(xs) + MARGIN
y0, y1 = min(ys) - MARGIN, max(ys) + MARGIN
W = x1 - x0
H = y1 - y0

context = []
for k, v in G.items():
    cx, cy = v['c']
    if x0 - 60 <= cx <= x1 + 60 and y0 - 60 <= cy <= y1 + 60 and k not in SIGN_SET:
        context.append(k)


def path(rs):
    out = []
    for pts in rs:
        d = []
        for i, (x, y) in enumerate(pts):
            X = (x - x0)
            Y = (y1 - y)
            d.append(('M' if i == 0 else 'L') + f'{X:.1f} {Y:.1f}')
        out.append(''.join(d) + 'Z')
    return ''.join(out)


ctx_paths = ''.join(f'<path d="{path(G[k]["rings"])}"/>' for k in context)
sig_paths = []
for p in sig:
    g = gname[p]
    cx, cy = G[p]['c']
    sig_paths.append(
        f'<path class="s g{g}" d="{path(G[p]["rings"])}"><title>{p} — {G[p]["povrsina"]} m²</title></path>')
sig_paths = ''.join(sig_paths)

lbls = ''.join(
    f'<text x="{G[p]["c"][0]-x0:.0f}" y="{y1-G[p]["c"][1]:.0f}">{p}</text>' for p in sig)

# ---- findings ----
missing = [p for p in UNIQUE if p not in G]
dupes = {}
for o, ps, m in OWNERS:
    for p in ps:
        dupes.setdefault(p, []).append(o)
conflicts = {p: v for p, v in dupes.items() if len(v) > 1}

rows = []
for o, ps, m in OWNERS:
    for p in ps:
        d = G.get(p)
        rows.append({
            'owner': o, 'p': p, 'mode': m,
            'ok': d is not None,
            'area': d['povrsina'] if d else None,
            'status': d['status'] if d else None,
            'grp': gname.get(p),
            'conflict': p in conflicts,
        })

json.dump({'rows': rows, 'groups': [[p for p in g] for g in groups],
           'missing': missing, 'conflicts': conflicts,
           'W': W, 'H': H, 'nctx': len(context)},
          open('report.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


print('sig', len(sig), 'missing', missing, 'ctx', len(context))
print('W %.0f H %.0f' % (W, H))
for i, g in enumerate(groups):
    ys_ = [G[p]['c'][1] for p in g]
    print(i, len(g), sorted(g))
print('conflicts', conflicts)
print('total area', sum(G[p]['povrsina'] for p in sig))
