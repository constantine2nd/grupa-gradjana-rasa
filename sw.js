---
layout: null
---
// Service worker -- Faza 1: instalabilnost i strana za offline.
//
// NAMERNO KESIRA SAMO offline.html. Faza 2 uvodi precache ljuske i strategije
// po tipu resursa; dok se to ne odluci, ovde nema nicega sto moze da ustajne.
// Spisak potpisnika se menja iz nedelje u nedelju, a stranica koja pokazuje
// prosli broj parcela gora je nego stranica koje nema.
//
// VERZIJA se menja pri svakom buildu (site.time), pa se stari kes brise sam.
//
// Ako ovo ikad zaglavi sajt posetiocima: bin/sw-kill.js prepisati preko ovog
// fajla i gurnuti. Taj fajl se sam odjavljuje i brise sve kesove.

const VERZIJA = 'v{{ site.time | date: "%Y%m%d%H%M%S" }}';
const KES = 'gg-rasa-' + VERZIJA;
const OFFLINE = '{{ "/offline.html" | relative_url }}';

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(KES)
      .then((c) => c.add(new Request(OFFLINE, { cache: 'reload' })))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((k) => Promise.all(
        k.filter((n) => n.startsWith('gg-rasa-') && n !== KES).map((n) => caches.delete(n))
      ))
      .then(() => self.clients.claim())
  );
});

// Samo navigacije. Sve ostalo ide pravo na mrezu -- bez respondWith, bez
// posrednika, tacno kao da service workera nema.
self.addEventListener('fetch', (e) => {
  if (e.request.mode !== 'navigate') return;
  e.respondWith(
    fetch(e.request).catch(() => caches.match(OFFLINE))
  );
});

// Stranica moze da zatrazi da nova verzija preuzme odmah.
self.addEventListener('message', (e) => {
  if (e.data === 'preuzmi-odmah') self.skipWaiting();
});
