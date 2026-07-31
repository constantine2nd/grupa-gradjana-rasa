import json, urllib.request, sys
import os as _os, sys as _sys
_os.chdir(_os.path.dirname(_os.path.abspath(__file__)) or '.')

U = 'https://a3.geosrbija.rs/WebServices/client/DataView.asmx/ReadFiltered'
T = '377ca5f3-cdf2-4852-8b6b-2dce86153e9e'
COLS = ["brparcele", "povrsina", "status_parcele_opis"]


def many(vals, limit=6000):
    fc = [{"name": "brparcele", "comparisonOperator": "ANY", "value": vals,
           "netType": "string[]", "logicalOperator": "AND"},
          {"name": "maticnibrojko", "comparisonOperator": "=", "value": 805408,
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


all_recs = {}
ranges = [(2300, 2400), (2600, 2800), (2900, 3000), (3000, 3120), (4600, 4720)]
for lo, hi in ranges:
    vals = gen(lo, hi)
    for i in range(0, len(vals), 1400):
        chunk = vals[i:i + 1400]
        try:
            r = many(chunk)
        except Exception as e:
            print("ERR", lo, hi, i, e, file=sys.stderr)
            continue
        for rec in (r.get('records') or []):
            all_recs[rec['brparcele']] = rec
        print(lo, hi, i, r['total'], len(all_recs), flush=True)

json.dump(all_recs, open('geoms.json', 'w', encoding='utf-8'), ensure_ascii=False)
print("TOTAL", len(all_recs))
