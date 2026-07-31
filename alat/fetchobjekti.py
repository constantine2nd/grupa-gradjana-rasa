# -*- coding: utf-8 -*-
"""Preuzima objekte (zgrade) po parcelama iz DKP sloja "Objekti".

Adresni registar (ulica + kucni broj) je zatvoren za citanje, a "potes" iz
A lista operata ne postoji ni u jednom otvorenom sloju. Ovo je jedino sto se
o izgradjenosti parcele moze dobiti automatski: povrsina pod objektom i
nacin koriscenja.

Izlaz: objekti.json  ->  {"2697": {"n": 1, "m2": 48, "vrste": [...]}, ...}
"""
import json, urllib.request, sys, os as _os
_os.chdir(_os.path.dirname(_os.path.abspath(__file__)) or '.')

U = 'https://a3.geosrbija.rs/WebServices/client/DataView.asmx/ReadFiltered'
THEME_OBJEKTI = '03514aa8-9f12-4a55-a1ef-805adee8f779'
KO = 805408
COLS = ["brparcele", "brdelaparc", "povrsina", "nacin_koiscenja_opis", "opisobjekta"]

exec(open('build.py', encoding='utf-8').read().split('# ---- clusters')[0])
parcels = sorted(SIGN_SET)


def fetch(vals):
    fc = [{"name": "brparcele", "comparisonOperator": "ANY", "value": vals,
           "netType": "string[]", "logicalOperator": "AND"},
          {"name": "maticnibrojko", "comparisonOperator": "=", "value": KO,
           "netType": "int", "logicalOperator": "AND"}]
    body = {"theme_uuid": THEME_OBJEKTI, "columns": COLS,
            "filter": {"greedy": True, "filterColumns": fc}, "start": 0, "limit": 2000}
    req = urllib.request.Request(U, json.dumps(body).encode(),
                                 {'Content-Type': 'application/json; charset=utf-8'})
    return json.load(urllib.request.urlopen(req, timeout=180))['d']


out = {}
for i in range(0, len(parcels), 400):
    r = fetch(parcels[i:i + 400])
    if not r.get('success'):
        print('GRESKA:', r.get('exception'), file=sys.stderr)
        continue
    for rec in (r.get('records') or []):
        e = out.setdefault(rec['brparcele'], {"n": 0, "m2": 0, "vrste": []})
        e["n"] += 1
        e["m2"] += rec.get('povrsina') or 0
        v = rec.get('nacin_koiscenja_opis') or rec.get('opisobjekta')
        if v and v not in e["vrste"]:
            e["vrste"].append(v)

json.dump(out, open('objekti.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'parcela sa objektom: {len(out)} / {len(parcels)}')
for p in sorted(out):
    print(f'  {p:8s} {out[p]["n"]} obj  {out[p]["m2"]:5d} m²  {", ".join(out[p]["vrste"])}')
