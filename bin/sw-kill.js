// PREKIDAC ZA NUZDU -- ovaj fajl se NE isporucuje ovakav kakav je.
//
// Service worker je lepljiv. Kad ga pregledac jednom pokupi, on kontrolise
// sajt i pri sledecim posetama, pa pokvaren service worker ne popravlja
// obican deploy -- posetiocu i dalje odgovara stari.
//
// Ako se to desi:
//
//     cp bin/sw-kill.js sw.js && git commit -am "Skini service worker" && git push
//
// Cim posetilac otvori sajt, ova verzija se odjavljuje, brise sve kesove i
// osvezava otvorene kartice. Posle toga sajt radi kao da service workera
// nikad nije ni bilo.
//
// Kada je odradio svoje, sw.js se vraca iz gita:
//
//     git checkout <commit-pre-gasenja> -- sw.js
//
// Ostaviti ga bar nedelju dana, da ga pokupe i oni koji ne svracaju svaki dan.

self.addEventListener('install', () => self.skipWaiting());

self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    const imena = await caches.keys();
    await Promise.all(imena.map((n) => caches.delete(n)));
    await self.registration.unregister();
    const klijenti = await self.clients.matchAll({ type: 'window' });
    klijenti.forEach((k) => k.navigate(k.url));
  })());
});
