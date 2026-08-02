---
layout: null
---
// Service worker -- Faza 2: sajt radi bez interneta.
//
// VERZIJA dolazi iz site.time, pa svaki build pravi nove kesove i brise stare.
//
// Strategije po tipu, jer im se potrebe razlikuju:
//
//   HTML          mreza pa kes.  Spisak potpisnika se menja iz nedelje u
//                 nedelju; stranica koja pokazuje prosli broj parcela gora je
//                 od stranice koje nema. Kes je ovde rezerva, ne izvor.
//   CSS/JS/font   kes pa tiho osvezavanje u pozadini. Nose otisak builda samo
//                 preko VERZIJE, pa se pri svakom deployu ionako povuku nanovo.
//   slike         kes pa mreza, sa gornjom granicom. Ne menjaju se, a velike su.
//   tudji domeni  ne diramo. Google Analytics offline neka slobodno padne.
//
// PRECACHE je rucni spisak. Namerno: cache.addAll bi pao ceo ako jedan fajl
// fali, pa se svaki dodaje zasebno i promasaj se samo prijavi. Ako se neki
// fajl preimenuje, service worker nastavlja da radi, samo taj nije unapred tu.
//
// Prekidac za nuzdu ako ovo zaglavi sajt: bin/sw-kill.js

const VERZIJA = 'v{{ site.time | date: "%Y%m%d%H%M%S" }}';
const KES_LJUSKA = 'gg-rasa-ljuska-' + VERZIJA;
const KES_STRANICE = 'gg-rasa-stranice-' + VERZIJA;
const KES_SLIKE = 'gg-rasa-slike-' + VERZIJA;
const NASI_KESOVI = [KES_LJUSKA, KES_STRANICE, KES_SLIKE];

const OFFLINE = '{{ "/offline.html" | relative_url }}';
const MAX_SLIKA = 40;

const PRECACHE = [
  '{{ "/" | relative_url }}',
  OFFLINE,
  // Katastarski plan -- jedina stranica koju neko stvarno otvara u ataru,
  // gde signala nema. Zbog nje sve ovo i postoji.
  '{{ "/inicijativa-za-asfaltiranje-puta-i-opticki-internet.html" | relative_url }}',
  '{{ "/assets/main.css" | relative_url }}',
  '{{ "/assets/scripts.js" | relative_url }}',
  '{{ "/assets/vendor/jquery/jquery-3.5.1.min.js" | relative_url }}',
  '{{ "/assets/vendor/bootstrap/js/bootstrap.bundle.min.js" | relative_url }}',
  '{{ "/assets/vendor/startbootstrap-clean-blog/js/scripts.js" | relative_url }}',
  // Samo uspravni rezovi. Kurziv se koristi retko (citat, potpis ispod slike)
  // i sacekace da ga runtime kes pokupi -- 146 KB manje na prvoj poseti,
  // a bas ta poseta je najcesce sa telefona na slabom signalu.
  '{{ "/assets/fonts/lora-latin.woff2" | relative_url }}',
  '{{ "/assets/fonts/lora-latin-ext.woff2" | relative_url }}',
  '{{ "/assets/fonts/opensans-latin.woff2" | relative_url }}',
  '{{ "/assets/fonts/opensans-latin-ext.woff2" | relative_url }}',
  '{{ "/assets/icons/icon-192.png" | relative_url }}',
  '{{ "/assets/icons/favicon.svg" | relative_url }}',
];

// ---------- instalacija ----------

self.addEventListener('install', (e) => {
  e.waitUntil((async () => {
    const kes = await caches.open(KES_LJUSKA);
    const ishodi = await Promise.allSettled(
      PRECACHE.map((u) => kes.add(new Request(u, { cache: 'reload' })))
    );
    const pali = ishodi
      .map((r, i) => (r.status === 'rejected' ? PRECACHE[i] : null))
      .filter(Boolean);
    if (pali.length) console.warn('Precache promasio:', pali);
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    const imena = await caches.keys();
    await Promise.all(
      imena
        .filter((n) => n.startsWith('gg-rasa-') && !NASI_KESOVI.includes(n))
        .map((n) => caches.delete(n))
    );
    await self.clients.claim();
  })());
});

// ---------- strategije ----------

async function mrezaPaKes(req, imeKesa) {
  const kes = await caches.open(imeKesa);
  try {
    const odg = await fetch(req);
    if (odg && odg.ok) kes.put(req, odg.clone());
    return odg;
  } catch (err) {
    const iz_kesa = (await kes.match(req)) || (await caches.match(req));
    if (iz_kesa) return iz_kesa;
    throw err;
  }
}

async function kesPaTihoOsvezi(req, imeKesa) {
  const kes = await caches.open(imeKesa);
  const iz_kesa = await kes.match(req);
  const sa_mreze = fetch(req)
    .then((odg) => {
      if (odg && odg.ok) kes.put(req, odg.clone());
      return odg;
    })
    .catch(() => null);
  return iz_kesa || (await sa_mreze) || Promise.reject(new Error('nema ni u kesu ni na mrezi'));
}

async function kesPaMreza(req, imeKesa, granica) {
  const kes = await caches.open(imeKesa);
  const iz_kesa = await kes.match(req);
  if (iz_kesa) return iz_kesa;
  const odg = await fetch(req);
  if (odg && odg.ok) {
    await kes.put(req, odg.clone());
    if (granica) orezi(imeKesa, granica);
  }
  return odg;
}

// Cache API nema ogranicenje velicine, pa najstarije izbacujemo sami.
// Redosled keys() je redosled upisa, tako da su prvi ujedno i najstariji.
async function orezi(imeKesa, granica) {
  const kes = await caches.open(imeKesa);
  const kljucevi = await kes.keys();
  if (kljucevi.length <= granica) return;
  await Promise.all(kljucevi.slice(0, kljucevi.length - granica).map((k) => kes.delete(k)));
}

// ---------- razvrstavanje ----------

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  // Tudji domeni prolaze netaknuti: analitika, kontakt forma. Njihovi odgovori
  // su neprozirni, ne moze im se ni proveriti status, a kes bi trosili naslepo.
  if (url.origin !== self.location.origin) return;

  if (req.mode === 'navigate') {
    e.respondWith(
      mrezaPaKes(req, KES_STRANICE).catch(() => caches.match(OFFLINE))
    );
    return;
  }

  const dest = req.destination;
  if (dest === 'style' || dest === 'script' || dest === 'font') {
    e.respondWith(kesPaTihoOsvezi(req, KES_LJUSKA));
  } else if (dest === 'image') {
    e.respondWith(kesPaMreza(req, KES_SLIKE, MAX_SLIKA).catch(() => fetch(req)));
  }
  // sve ostalo: bez respondWith, ide pravo na mrezu
});

self.addEventListener('message', (e) => {
  if (e.data === 'preuzmi-odmah') self.skipWaiting();
});
