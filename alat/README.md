# Alat za katastarski plan inicijative

Skripte koje prave stranicu
[`/inicijativa-za-asfaltiranje-puta-i-opticki-internet.html`](../inicijativa-za-asfaltiranje-puta-i-opticki-internet.html)
— katastarski plan parcela sa potpisnog spiska i puta 7810/2 na koji izlaze.

Podaci se povlače iz digitalnog katastarskog plana Republičkog geodetskog zavoda.
Plan je ugrađen u stranicu kao SVG, pa nema spoljnih zahteva: radi i bez interneta
i ne može da se pokvari kad neki CDN nestane.

---

## Ponovo napraviti stranicu

```bash
python3 alat/napravi.py
```

To je sve. Skripta redom pokrene `gen.py` (crta plan i obe verzije stranice),
`translit.py` (ćirilica u latinicu) i `standalone.py` (uvija javnu verziju u pun
HTML dokument i smešta je u koren sajta). Posle toga samo `git add` i `push`.

## Lični podaci

**Spisak potpisnika stoji u `alat/spisak.py`, koji se ne komituje.** Naveden je u
`alat/.gitignore` zajedno sa `_izlaz/` i `report.json`. Sve ostalo u ovom
direktorijumu je bez ličnih podataka.

Prvi put:

```bash
cp alat/spisak.primer.py alat/spisak.py     # pa upisati prave podatke
```

`gen.py` pravi dve stranice:

| Stranica | Gde završi | Sadržaj |
|---|---|---|
| javna | koren sajta, komituje se | zaglavlje, plan, legenda — **bez ijednog imena** |
| interna | `alat/_izlaz/`, ignorisana | imena, tabela, nalazi, suvlasništva |

Posle generisanja `gen.py` **pretraži javnu stranicu za svako ime** iz `OWNERS` i
`SUVLASNISTVO` i prekine sa greškom ako ijedno nađe. Ako neko doda tekst sa imenom
u `page-javno.tmpl.html`, build neće proći.

## Kad se spisak proširi

1. U `alat/spisak.py` dodati red u `OWNERS`:
   `("Ime Prezime", ["2945", "2947"], "oba")` — treći član je `"oba"`, `"asfalt"`
   ili `"internet"`.
2. Ako je nova parcela van opsega brojeva u `fetchgeom.py`, dodati opseg u `ranges`
   i pokrenuti `python3 alat/fetchgeom.py`. Za nove objekte na parcelama
   `python3 alat/fetchobjekti.py`.
3. `python3 alat/napravi.py`

Razvrstavanje po odnosu na put i rastojanja računaju se sama. **Tekst u sekciji
„Nalazi" u `page.tmpl.html` pisan je rukom** — pročitati ga posle svake izmene,
jer tvrdnje u njemu ne prate spisak automatski.

---

## Odakle podaci

Interni servis `a3.geosrbija.rs`. Bez ključa, bez naloga, bez captche.

```
POST https://a3.geosrbija.rs/WebServices/client/DataView.asmx/ReadFiltered
Content-Type: application/json

{"theme_uuid":"377ca5f3-cdf2-4852-8b6b-2dce86153e9e",
 "columns":["brparcele","povrsina","kat_opstina_imel","status_parcele_opis"],
 "filter":{"greedy":true,"filterColumns":[
   {"name":"brparcele","comparisonOperator":"=","value":"2885/1",
    "netType":"string","logicalOperator":"AND"},
   {"name":"maticnibrojko","comparisonOperator":"=","value":805408,
    "netType":"int","logicalOperator":"AND"}]},
 "start":0,"limit":50}
```

Odgovor je uvijen u `{"d":{...}}` i uz tražene kolone uvek vraća i `geom_wkt`
(MULTIPOLYGON u **EPSG:32634**, UTM zona 34N, metri).

| | |
|---|---|
| `theme_uuid` sloja „Parcele (Vojvodina)" | `377ca5f3-cdf2-4852-8b6b-2dce86153e9e` |
| `theme_uuid` sloja „Objekti" | `03514aa8-9f12-4a55-a1ef-805adee8f779` |
| `maticnibrojko` za KO Sremski Karlovci | `805408` |
| GUID aplikacije Geosrbija | `1d1766e8-0ab8-444a-b8ac-6708698bca4b` |

Ako se `theme_uuid` promeni, novi se vadi iz konfiguracije aplikacije:

```bash
curl -s -X POST https://a3.geosrbija.rs/WebServices/client/Configuration.asmx/ReadAppConfig \
  -H 'Content-Type: application/json' \
  -d '{"guuid":"1d1766e8-0ab8-444a-b8ac-6708698bca4b"}' > cfg.json
# u cfg.json naći sloj sa "layers": "layer_827", pa u njegovom theme_data -> theme_uuid
```

Kopija metapodataka tog sloja, sa svim kolonama, je u `theme827.json`.

**Dve zamke**

- `filter` mora biti **objekat**, ne JSON string — string vraća HTTP 500.
- `LIKE` ne radi. Za više parcela odjednom: `"comparisonOperator":"ANY"` uz
  `"netType":"string[]"` i niz vrednosti. Prolazi oko 1.400 vrednosti po zahtevu.

---

## Šta gde stoji

| Fajl | Sadržaj |
|---|---|
| `napravi.py` | Cela izrada u jednoj komandi |
| `spisak.py` | **Spisak potpisnika — ne komituje se** |
| `spisak.primer.py` | Predložak, sa izmišljenim imenima |
| `check.py` | Provera parcela jedne po jedne, sa punim odgovorom servisa |
| `fetchgeom.py` | Masovno preuzimanje geometrija po opsezima brojeva (`ranges`) |
| `fetchput.py` | Geometrija puta 7810/1, 7810/2, 7810/3 |
| `fetchobjekti.py` | Površina pod zgradama, po parceli |
| `build.py` | Spaja spisak sa geometrijama |
| `gen.py` | Razvrstavanje, rastojanja, SVG plan, tabela, obe stranice |
| `standalone.py` | Uvija fragment u pun HTML dokument |
| `translit.py` | Srpska ćirilica → latinica, samo nad ćiriličnim znakovima |
| `page.tmpl.html` | Predložak interne stranice; `%%TOKEN%%` popunjava `gen.py` |
| `page-javno.tmpl.html` | Predložak javne stranice — bez imena i bez tabele |
| `geoms.json` | 1.152 parcele sa geometrijom (opsezi 2300–3120 i 4600–4720) |
| `put.json` | Geometrija puta |
| `objekti.json` | Zgrade po parceli: broj i ukupna površina |
| `results.json` | Rezultat provere po parceli, centroidi u WGS84 |
| `theme827.json` | Metapodaci sloja parcela |
| `dkp_swagger.json` | Dokumentacija zvaničnog REST API-ja RGZ-a (traži token) |

---

## Kako se računaju grupe

Merilo je **rastojanje do puta 7810/2**, ne međusobna blizina parcela. Za svako
teme parcele traži se najbliža duž poligona puta; uzima se najmanje rastojanje.
Pragovi su u `gen.py`:

- `ON_ROAD = 5` m → *izlazi na put*
- do `BEHIND = 300` m → *zaleđe* uz istu trasu
- preko toga → *van trase*

Geometrija je već u metrima (UTM 34N) pa se rastojanja računaju direktno.
`pyproj` treba samo `check.py`, za centroide u WGS84.

**Zašto ne klasterovanje.** Prva verzija je grupisala parcele po međusobnoj
blizini i dobijala „jezgro / sever / jug". To je davalo pogrešan zaključak:
severne parcele izgledale su kao odvojen krak jer su 270–420 m od jezgra, a
zapravo sve izlaze direktno na isti put. Put je organizaciono načelo, ne blizina.

---

## Šta se NE može dobiti

**Vlasništvo.** Imena vlasnika nisu dostupna kroz servise Geosrbije. Jedini javni
izvor je eKatastar (`katastar.rgz.gov.rs/eKatastarPublic`), a forma
`FindParcela.aspx?KoID=805408` ima SVG captchu na svakoj pretrazi. Zato se B
listovi vade ručno i upisuju u `SUVLASNISTVO` u `spisak.py`.

**Ulica i kućni broj.** „Потес / Улица" iz eKatastra je podatak iz A lista
operata. Za poljoprivredne parcele to je *potes* (ime lokaliteta, npr. RAŠA), a
ne ulica — u adresnom registru opštine Sremski Karlovci nema nijedne od 210 ulica
pod tim imenom. Sloj adresnog registra „Kućni broj"
(`56dd695b-4f2c-45cc-91cc-fdbd7121ed6f`) ima baš polja za spajanje po broju
parcele, ali vraća `{"success":false,"exception":{"msg":"Dataview access disabled"}}`.
Kao zamena se koristi sloj „Objekti", koji daje površinu pod zgradama.

**Zvanični REST API.** Isti podaci postoje na
`rest.geosrbija.rs/api/dkp/v1/parcela` (dokumentacija u `dkp_swagger.json`), ali
traži token koji se dobija registracijom kod RGZ-a — `nsdi@rgz.gov.rs`. Ako se
token nabavi, to je stabilniji put od internog servisa korišćenog ovde.

**Deonica koja se traži.** Put 7810/2 je ucrtan ceo, preko 2 km. Koji njegov deo
inicijativa traži da se asfaltira nije podatak iz katastra i treba ga odlučiti.
