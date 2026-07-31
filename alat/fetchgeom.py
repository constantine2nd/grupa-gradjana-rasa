# -*- coding: utf-8 -*-
"""Preuzima geometrije parcela iz digitalnog katastarskog plana u geoms.json.

Podrazumevano DOPUNJUJE: pita servis samo za parcele sa spiska potpisnika kojih
u geoms.json jos nema. Kad se spisku doda jedan potpisnik, to je jedan zahtev za
jednu parcelu, a ne ponovo hiljadu i po.

    python3 alat/fetchgeom.py              dopuni po spisku (uobicajeno)
    python3 alat/fetchgeom.py 2945 3011/1  dopuni i ovim brojevima
    python3 alat/fetchgeom.py --sve        pun prolaz kroz opsege (~1.150 parcela)

Pun prolaz treba samo kad se plan siri na novo podrucje, pa uz potpisnike zatreba
i novi pojas susednih parcela koje se crtaju kao tanke sive konture. Za obicno
dodavanje potpisnika nije potreban.
"""
import json, urllib.request, sys, os

os.chdir(os.path.dirname(os.path.abspath(__file__)) or '.')

U = 'https://a3.geosrbija.rs/WebServices/client/DataView.asmx/ReadFiltered'
T = '377ca5f3-cdf2-4852-8b6b-2dce86153e9e'
COLS = ["brparcele", "povrsina", "status_parcele_opis"]
KO = 805408            # maticni broj KO Sremski Karlovci
CHUNK = 1400           # koliko vrednosti stane u jedan ANY filter

# Opsezi za pun prolaz. Koriste se samo uz --sve.
RANGES = [(2300, 2400), (2600, 2800), (2900, 3000), (3000, 3120), (4600, 4720)]


def many(vals, limit=6000):
    fc = [{"name": "brparcele", "comparisonOperator": "ANY", "value": vals,
           "netType": "string[]", "logicalOperator": "AND"},
          {"name": "maticnibrojko", "comparisonOperator": "=", "value": KO,
           "netType": "int", "logicalOperator": "AND"}]
    body = {"theme_uuid": T, "columns": COLS,
            "filter": {"greedy": True, "filterColumns": fc}, "start": 0, "limit": limit}
    req = urllib.request.Request(U, json.dumps(body).encode(),
                                 {'Content-Type': 'application/json; charset=utf-8'})
    return json.load(urllib.request.urlopen(req, timeout=300))['d']


def gen(lo, hi):
    out = []
    for n in range(lo, hi + 1):
        out.append(str(n))
        for s in range(1, 7):
            out.append(f"{n}/{s}")
    return out


def preuzmi(vals, recs, oznaka=''):
    """Pita servis za date brojeve i upisuje nadjeno u recs."""
    pre = len(recs)
    for i in range(0, len(vals), CHUNK):
        chunk = vals[i:i + CHUNK]
        try:
            r = many(chunk)
        except Exception as e:
            print("GRESKA", oznaka, i, e, file=sys.stderr)
            continue
        for rec in (r.get('records') or []):
            recs[rec['brparcele']] = rec
        if len(vals) > CHUNK:
            print(f'  {oznaka} {i:>5}  ukupno u bazi {r["total"]:>5}  '
                  f'skupljeno {len(recs)}', flush=True)
    return len(recs) - pre


def sa_spiska():
    """Brojevi parcela iz spisak.py -- potpisnici i suvlasnistva."""
    ns = {}
    try:
        exec(open('spisak.py', encoding='utf-8').read(), ns)
    except FileNotFoundError:
        sys.exit('nema spisak.py -- vidi spisak.primer.py')
    ps = {p for _, parc, _ in ns.get('OWNERS', []) for p in parc}
    ps |= set(ns.get('SUVLASNISTVO', {}))
    return ps


args = sys.argv[1:]
sve = '--sve' in args
rucno = [a for a in args if not a.startswith('--')]

geoms = {}
if os.path.exists('geoms.json'):
    geoms = json.load(open('geoms.json', encoding='utf-8'))
pre = len(geoms)

if sve:
    print(f'pun prolaz kroz {len(RANGES)} opsega -- ovo je onih ~1.150 parcela')
    for lo, hi in RANGES:
        preuzmi(gen(lo, hi), geoms, f'{lo}-{hi}')
else:
    trazi = sorted((sa_spiska() | set(rucno)) - set(geoms))
    if not trazi:
        print(f'geoms.json vec ima sve sa spiska ({pre} parcela) -- nema sta da se preuzme')
        sys.exit(0)
    print(f'nedostaje {len(trazi)}: {", ".join(trazi)}')
    preuzmi(trazi, geoms, 'spisak')
    jos_nema = [p for p in trazi if p not in geoms]
    if jos_nema:
        print('katastar ih ne zna pod tim brojem:', ', '.join(jos_nema), file=sys.stderr)

json.dump(geoms, open('geoms.json', 'w', encoding='utf-8'), ensure_ascii=False)
print(f'geoms.json: {pre} -> {len(geoms)} parcela (+{len(geoms)-pre})')
