import json, urllib.request, time, sys
import os as _os, sys as _sys
_os.chdir(_os.path.dirname(_os.path.abspath(__file__)) or '.')
from pyproj import Transformer

U = 'https://a3.geosrbija.rs/WebServices/client/DataView.asmx/ReadFiltered'
THEMES = {
    'Vojvodina': '377ca5f3-cdf2-4852-8b6b-2dce86153e9e',
}
COLS = ["brparcele", "povrsina", "kat_opstina_imel", "opstina_imel",
        "maticnibrojko", "status_parcele_opis", "dkp_status_opis", "in_date"]
KO_SK = 805408
tr = Transformer.from_crs("EPSG:32634", "EPSG:4326", always_xy=True)


def call(body):
    req = urllib.request.Request(U, json.dumps(body).encode(),
                                 {'Content-Type': 'application/json; charset=utf-8'})
    return json.load(urllib.request.urlopen(req, timeout=90))['d']


def query(parcela, ko=None, theme=THEMES['Vojvodina']):
    fc = [{"name": "brparcele", "comparisonOperator": "=", "value": parcela,
           "netType": "string", "logicalOperator": "AND"}]
    if ko:
        fc.append({"name": "maticnibrojko", "comparisonOperator": "=", "value": ko,
                   "netType": "int", "logicalOperator": "AND"})
    return call({"theme_uuid": theme, "columns": COLS,
                 "filter": {"greedy": True, "filterColumns": fc},
                 "start": 0, "limit": 50})


def centroid(wkt):
    """crude centroid of first ring of a MULTIPOLYGON/POLYGON wkt"""
    s = wkt[wkt.find('(') :]
    s = s.lstrip('(')
    s = s[:s.find(')')]
    pts = []
    for p in s.split(','):
        p = p.strip().strip('(').strip().split()
        if len(p) >= 2:
            pts.append((float(p[0]), float(p[1])))
    n = len(pts)
    x = sum(p[0] for p in pts) / n
    y = sum(p[1] for p in pts) / n
    lon, lat = tr.transform(x, y)
    return x, y, lat, lon


# Spisak stoji u spisak.py (licni podaci, ne komituje se).
exec(open('spisak.py', encoding='utf-8').read())

results = {}
for owner, parcels, _mode in OWNERS:
    for p in parcels:
        if p in results:
            continue
        try:
            r = query(p, KO_SK)
        except Exception as e:
            print("ERR", p, e, file=sys.stderr)
            time.sleep(2)
            try:
                r = query(p, KO_SK)
            except Exception as e2:
                results[p] = {"error": str(e2)}
                continue
        recs = r.get('records') or []
        if recs:
            rec = recs[0]
            cx, cy, lat, lon = centroid(rec['geom_wkt'])
            results[p] = {"found": True, "n": len(recs), "povrsina": rec['povrsina'],
                          "status": rec['status_parcele_opis'], "ko": rec['kat_opstina_imel'],
                          "lat": lat, "lon": lon, "x": cx, "y": cy,
                          "dkp": rec.get('dkp_status_opis'), "in_date": rec.get('in_date')}
        else:
            results[p] = {"found": False}
        print(p, results[p].get('found'), results[p].get('povrsina', ''), flush=True)

json.dump(results, open('results.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print("MISSING:", [p for p, v in results.items() if not v.get('found')])
