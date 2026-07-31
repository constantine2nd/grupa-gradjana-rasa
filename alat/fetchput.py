# -*- coding: utf-8 -*-
"""Preuzima geometriju puta 7810/1, 7810/2 i 7810/3 -> put.json.

7810/2 je glavna trasa (13.723 m², preko 2 km); 7810/1 i 7810/3 su nastavci na
severnom kraju. Po ovim geometrijama gen.py racuna rastojanje svake parcele do
puta i crta ga na planu.
"""
import json, urllib.request, os as _os
_os.chdir(_os.path.dirname(_os.path.abspath(__file__)) or '.')

U = 'https://a3.geosrbija.rs/WebServices/client/DataView.asmx/ReadFiltered'
THEME = '377ca5f3-cdf2-4852-8b6b-2dce86153e9e'
KO = 805408
DELOVI = ["7810/1", "7810/2", "7810/3"]

fc = [{"name": "brparcele", "comparisonOperator": "ANY", "value": DELOVI,
       "netType": "string[]", "logicalOperator": "AND"},
      {"name": "maticnibrojko", "comparisonOperator": "=", "value": KO,
       "netType": "int", "logicalOperator": "AND"}]
body = {"theme_uuid": THEME,
        "columns": ["brparcele", "povrsina", "status_parcele_opis"],
        "filter": {"greedy": True, "filterColumns": fc}, "start": 0, "limit": 20}
req = urllib.request.Request(U, json.dumps(body).encode(),
                             {'Content-Type': 'application/json; charset=utf-8'})
recs = json.load(urllib.request.urlopen(req, timeout=120))['d']['records'] or []
json.dump({x['brparcele']: x for x in recs},
          open('put.json', 'w', encoding='utf-8'), ensure_ascii=False)
for x in sorted(recs, key=lambda r: r['brparcele']):
    print(f"  {x['brparcele']:8s} {x['povrsina']:6d} m²  {x['status_parcele_opis']}")
