# -*- coding: utf-8 -*-
"""UTM zona 34N (EPSG:32634) -> geografske koordinate WGS84.

Katastar isporucuje geometriju u metrima, UTM 34N. Za "otvori u mapama" trebaju
stepeni, pa negde mora da stoji obrnuta projekcija.

Racuna se ovde umesto kroz pyproj da `napravi.py` ne bi dobio novu zavisnost --
do sada je pyproj trebao samo `check.py`, koji se pokrece rucno i retko. Formula
je klasican razvoj u red za inverznu poprecnu Merkatorovu projekciju; tacnost je
milimetarska unutar zone, sto je red velicine bolje nego sto katastarski plan
uopste tvrdi.

Tacnost se ne uzima na veru: `proveri.py` poredi ovo sa pyproj-om na centroidima
svih parcela sa spiska.
"""
import math

# WGS84
A = 6378137.0
F = 1 / 298.257223563
E2 = F * (2 - F)               # kvadrat prvog ekscentriciteta
EP2 = E2 / (1 - E2)            # kvadrat drugog ekscentriciteta
K0 = 0.9996                    # razmera na centralnom meridijanu, UTM
E0 = 500000.0                  # istocni pomeraj, UTM


def zona_meridijan(zona):
    """Centralni meridijan zone, u stepenima. Za zonu 34 to je 21."""
    return 6 * zona - 183


def u_wgs84(x, y, zona=34):
    """(istok, sever) u metrima -> (sirina, duzina) u stepenima.

    Vazi za severnu hemisferu; za juznu bi se od `y` oduzimalo 10.000.000.
    """
    m = y / K0
    e1 = (1 - math.sqrt(1 - E2)) / (1 + math.sqrt(1 - E2))
    mu = m / (A * (1 - E2 / 4 - 3 * E2 ** 2 / 64 - 5 * E2 ** 3 / 256))

    # geografska sirina tacke na centralnom meridijanu sa istim rastojanjem po luku
    fi1 = (mu
           + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * math.sin(2 * mu)
           + (21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32) * math.sin(4 * mu)
           + (151 * e1 ** 3 / 96) * math.sin(6 * mu)
           + (1097 * e1 ** 4 / 512) * math.sin(8 * mu))

    sin_fi1, cos_fi1, tan_fi1 = math.sin(fi1), math.cos(fi1), math.tan(fi1)
    c1 = EP2 * cos_fi1 ** 2
    t1 = tan_fi1 ** 2
    n1 = A / math.sqrt(1 - E2 * sin_fi1 ** 2)                 # poluprecnik prve vertikale
    r1 = A * (1 - E2) / (1 - E2 * sin_fi1 ** 2) ** 1.5        # poluprecnik meridijana
    d = (x - E0) / (n1 * K0)

    sirina = fi1 - (n1 * tan_fi1 / r1) * (
        d ** 2 / 2
        - (5 + 3 * t1 + 10 * c1 - 4 * c1 ** 2 - 9 * EP2) * d ** 4 / 24
        + (61 + 90 * t1 + 298 * c1 + 45 * t1 ** 2 - 252 * EP2 - 3 * c1 ** 2) * d ** 6 / 720)

    duzina = (d
              - (1 + 2 * t1 + c1) * d ** 3 / 6
              + (5 - 2 * c1 + 28 * t1 - 3 * c1 ** 2 + 8 * EP2 + 24 * t1 ** 2) * d ** 5 / 120
              ) / cos_fi1

    return math.degrees(sirina), zona_meridijan(zona) + math.degrees(duzina)
