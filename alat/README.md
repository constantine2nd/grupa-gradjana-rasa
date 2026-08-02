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

`standalone.py` u zaglavlje upisuje i `manifest.webmanifest`, ikone i registraciju
service workera — **relativnim putanjama**, jer ova stranica ne prolazi kroz Jekyll
pa `relative_url` ne postoji, a `baseurl` se ne sme ukucati rukom. Pošto stranica
stoji u korenu sajta, pored `manifest.webmanifest` i `sw.js`, iste putanje rade i
kad se sajt servira i kad se fajl otvori sa diska.

Bez toga plan je bio jedina stranica koja ne registruje service worker: ko dobije
link baš na njega i otvori ga prvi put, ne dobije ništa keširano — a to je jedina
stranica koju neko stvarno otvara u ataru, gde signala nema.

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
2. `python3 alat/fetchgeom.py` — sam pogleda spisak i preuzme **samo parcele kojih
   u `geoms.json` još nema**. Za jednog novog potpisnika to je jedan zahtev za
   jednu parcelu. Za nove objekte na parcelama `python3 alat/fetchobjekti.py`.
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

## Koliko se podataka uzima

`geoms.json` je nastao jednim širokim prolazom kroz opsege brojeva i u njemu je
1.152 parcele. Od toga se stvarno koristi 772: 64 sa spiska i 708 susednih, koje
se na planu crtaju kao tanke sive konture radi orijentacije. Ostalih 380 je
višak iz tog prvog prolaza.

**Taj široki prolaz se više ne ponavlja sam od sebe.** `fetchgeom.py` bez
argumenata pita servis samo za parcele sa spiska kojih u `geoms.json` nema — kad
se javi novi potpisnik, to je jedan zahtev za jednu parcelu. Pun prolaz ostaje
dostupan, ali se traži izričito:

```bash
python3 alat/fetchgeom.py              # dopuni po spisku (uobičajeno)
python3 alat/fetchgeom.py 2945 3011/1  # dopuni i ovim brojevima
python3 alat/fetchgeom.py --sve        # pun prolaz kroz opsege (~1.150)
```

`--sve` treba samo ako se plan proširi na novo područje, pa uz nove potpisnike
zatreba i nov pojas susednih parcela. Za obično dodavanje potpisnika ne treba.

---

## Šta gde stoji

| Fajl | Sadržaj |
|---|---|
| `napravi.py` | Cela izrada u jednoj komandi |
| `spisak.py` | **Spisak potpisnika — ne komituje se** |
| `spisak.primer.py` | Predložak, sa izmišljenim imenima |
| `check.py` | Provera parcela jedne po jedne, sa punim odgovorom servisa |
| `fetchgeom.py` | Geometrije parcela; podrazumevano samo ono što spisku nedostaje |
| `fetchput.py` | Geometrija puta 7810/1, 7810/2, 7810/3 |
| `fetchobjekti.py` | Površina pod zgradama, po parceli |
| `build.py` | Spaja spisak sa geometrijama |
| `gen.py` | Razvrstavanje, rastojanja, SVG plan, tabela, obe stranice |
| `standalone.py` | Uvija fragment u pun HTML dokument, dodaje manifest i service worker |
| `translit.py` | Srpska ćirilica → latinica, samo nad ćiriličnim znakovima |
| `page.tmpl.html` | Predložak interne stranice; `%%TOKEN%%` popunjava `gen.py` |
| `page-javno.tmpl.html` | Predložak javne stranice — bez imena i bez tabele |
| `geoms.json` | Geometrije parcela, već preuzete — spisak plus susedne za crtanje |
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

**Zvanični REST API — provereno, ne dolazi u obzir.** Isti podaci postoje na
`rest.geosrbija.rs/api/dkp/v1/parcela` (dokumentacija u `dkp_swagger.json`) i na
novijem v2 API-ju, ali oba su zatvorena za nas:

| | v1 | v2 |
|---|---|---|
| Host | `rest.geosrbija.rs` | samo `rest-tmp.geosrbija.rs` (test) |
| Menadžer naloga | nema ga — 404 | ima, ali test okruženje |
| Autentifikacija | `x-access-token`, trajni ključ | OAuth2 implicit, token traje minutima |

Katalog servisa navodi „Neophodan RGZID: Ne" i praznu kolonu za naplatu, što
vara. Odgovor NIGP tima RGZ-a od 31.07.2026. na direktno pitanje:

> Da biste koristili `rest-tmp.geosrbija.rs/rest-geosrbija/` potrebno je da budete
> profesionalni korisnik RGZ eUsluga. To postajete tako što na `id.rgz.gov.rs/rgzid/`
> registrujete nalog i podnosite zahtev za identifikacijom ovlašćenog lica
> (**potrebno je da je firma prijavljena u APR-u**). Nakon odobrenja stičete opštu
> licencu koja Vam **nakon izvršene uplate servisa** omogućava pristup. Plaćanje se
> vrši prema Zakonu o republičkim administrativnim taksama, **tarifni broj 215и**.

Znači: pravno lice iz APR-a plus plaćanje. Neformalna grupa građana ne ispunjava
ni prvi uslov. Uz to, dokumentacija v2 API-ja uz svaki endpoint ponavlja da se
„podaci dostavljeni demo korisnicima koriste ISKLJUČIVO u testne svrhe", pa se
njima ne bi smela hraniti javna stranica ni da pristup postoji.

**Put preko opštine.** Jedinice lokalne samouprave jesu u kategoriji kojoj su RGZ
eUsluge namenjene i **oslobođene su plaćanja takse**. Ako opština Sremski Karlovci
uđe u inicijativu kao partner, može da povuče iste podatke zvanično i besplatno.
To je jedini uredan put do zvaničnog izvora za ovaj projekat.

**Deonica koja se traži.** Put 7810/2 je ucrtan ceo, preko 2 km. Koji njegov deo
inicijativa traži da se asfaltira nije podatak iz katastra i treba ga odlučiti.
