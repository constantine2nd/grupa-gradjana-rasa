# -*- coding: utf-8 -*-
"""Pravi KML sa konturama parcela, za uvoz u mape.

    python3 alat/kml.py 3097 3096/1
    python3 alat/kml.py --spisak                # sve parcele sa potpisnog spiska
    python3 alat/kml.py 3097 -o /putanja/x.kml

Podrazumevano pise u alat/_izlaz/parcele.kml, koji se ne komituje.

Zasto KML a ne link ka mapama: nijedna mapa ne prima geometriju kroz URL --
Google Maps zna za tacku, pretragu i rutu, ne i za poligon. Kontura se moze
predati samo kao fajl. Ovaj otvaraju Google Earth, Google My Maps (Uvezi),
OsmAnd, Organic Maps, Locus i QGIS.

Koordinate su WGS84, iz koordinate.py -- isti racun koji stranica koristi za
"otvori u mapama", provereno u odnosu na pyproj do 0,1 mm.
"""
import json, os, sys

from koordinate import u_wgs84

HERE = os.path.dirname(os.path.abspath(__file__))

# KML boje su aabbggrr, ne rrggbb. Ovo je #0085A1 sa sajta.
POPUNA = '660085A1'[:2] + 'A18500'      # 66 = oko 40% neprovidnosti
LINIJA = 'ff' + 'A18500'


def prstenovi(wkt):
    """MULTIPOLYGON -> [[spoljni, rupa, ...], ...]. Prati dubinu zagrada."""
    out, poly, buf, dubina = [], [], '', 0
    for ch in wkt[wkt.index('('):]:
        if ch == '(':
            dubina += 1
            if dubina == 2:
                poly = []
            elif dubina == 3:
                buf = ''
        elif ch == ')':
            if dubina == 3:
                poly.append(buf)
            elif dubina == 2:
                out.append(poly)
            dubina -= 1
        elif dubina == 3:
            buf += ch
    return out


def kml_prsten(s):
    """Niz temena u UTM -> KML koordinate, lon,lat,0."""
    tacke = []
    for par in s.split(','):
        par = par.strip()
        if not par:
            continue
        x, y = map(float, par.split())
        lat, lon = u_wgs84(x, y)
        tacke.append(f'{lon:.7f},{lat:.7f},0')
    if tacke and tacke[0] != tacke[-1]:      # KML trazi zatvoren prsten
        tacke.append(tacke[0])
    return ' '.join(tacke)


def placemark(broj, rec):
    delovi = []
    for poly in prstenovi(rec['geom_wkt']):
        granice = f'<outerBoundaryIs><LinearRing><coordinates>{kml_prsten(poly[0])}' \
                  f'</coordinates></LinearRing></outerBoundaryIs>'
        for rupa in poly[1:]:
            granice += f'<innerBoundaryIs><LinearRing><coordinates>{kml_prsten(rupa)}' \
                       f'</coordinates></LinearRing></innerBoundaryIs>'
        delovi.append(f'<Polygon><tessellate>1</tessellate>{granice}</Polygon>')
    geom = delovi[0] if len(delovi) == 1 else '<MultiGeometry>' + ''.join(delovi) + '</MultiGeometry>'
    povrsina = f'{rec["povrsina"]:,}'.replace(',', '.')
    return (f'  <Placemark>\n'
            f'    <name>Parcela {broj}</name>\n'
            f'    <description>{povrsina} m² · KO Sremski Karlovci · '
            f'{rec.get("status_parcele_opis", "")}</description>\n'
            f'    <styleUrl>#parcela</styleUrl>\n'
            f'    {geom}\n'
            f'  </Placemark>')


if __name__ == '__main__':
    os.chdir(HERE)

    args = [a for a in sys.argv[1:]]
    dest = 'alat/_izlaz/parcele.kml'
    if '-o' in args:
        i = args.index('-o')
        dest = args[i + 1]
        del args[i:i + 2]
    else:
        dest = '_izlaz/parcele.kml'

    G = json.load(open('geoms.json', encoding='utf-8'))

    if '--spisak' in args:
        ns = __import__('runpy').run_path('spisak.py')
        brojevi = sorted({p for _, ps, _ in ns['OWNERS'] for p in ps})
    else:
        brojevi = args

    if not brojevi:
        sys.exit(__doc__)

    nema = [b for b in brojevi if b not in G]
    if nema:
        print('nema u geoms.json:', ', '.join(nema), file=sys.stderr)
        print('  (ako su van preuzetih opsega, dodati opseg u fetchgeom.py)', file=sys.stderr)
    brojevi = [b for b in brojevi if b in G]
    if not brojevi:
        sys.exit('nijedna parcela nije nadjena')

    telo = '\n'.join(placemark(b, G[b]) for b in brojevi)
    doc = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
  <name>Parcele — Raša, KO Sremski Karlovci</name>
  <description>Konture iz digitalnog katastarskog plana RGZ-a.</description>
  <Style id="parcela">
    <LineStyle><color>{LINIJA}</color><width>2</width></LineStyle>
    <PolyStyle><color>{POPUNA}</color></PolyStyle>
  </Style>
{telo}
</Document>
</kml>
'''

    os.makedirs(os.path.dirname(dest) or '.', exist_ok=True)
    open(dest, 'w', encoding='utf-8').write(doc)

    print(os.path.abspath(dest))
    print(f'  parcela: {len(brojevi)}  ({", ".join(brojevi)})')
    print(f'  {len(doc)} B')
