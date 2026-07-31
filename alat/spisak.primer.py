# -*- coding: utf-8 -*-
"""PREDLOZAK. Kopirajte u spisak.py i upisite prave podatke.

    cp alat/spisak.primer.py alat/spisak.py

spisak.py sadrzi licne podatke i naveden je u .gitignore -- ne komituje se.
Imena ispod su izmisljena, sluze samo da pokazu oblik.
"""

# (ime potpisnika, [brojevi parcela], za sta se prijavljuje)
# Treci clan: "oba", "asfalt" ili "internet".
OWNERS = [
    ("Petrović Petar", ["1234"], "oba"),
    ("Marković Ana i Zorka", ["1235/1", "1235/2"], "oba"),
    ("Ilić Mirko", ["1240"], "asfalt"),
]

# Suvlasnistvo potvrdjeno iz B lista eKatastra. Kljuc je broj parcele.
# Popunjava se rucno, kad se B list izvuce sa katastar.rgz.gov.rs/eKatastarPublic.
#
# Bez ovoga gen.py parcelu koju navodi vise potpisnika prijavljuje kao
# NERAZRESENU DVOSTRUKU PRIJAVU. Kad se upise ovde, tretira je kao potvrdjeno
# suvlasnistvo i broji upisane suvlasnike koji nisu na potpisnom spisku.
SUVLASNISTVO = {
    "1235/1": {
        "udeo": "1/3",
        "ukupno": 3,
        "datum": "01.01.2026.",
        "svi": ["Marković (Bogoljub) Ana",
                "Marković (Bogoljub) Zorka",
                "Nikolić (Sava) Vera"],
        "nepotpisali": ["Nikolić (Sava) Vera"],
    },
}
