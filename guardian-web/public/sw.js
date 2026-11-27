// Guardian HQ: service worker della sola "shell" statica (HTML, JS, CSS, icone).
// Non salva MAI i dati: le richieste verso Supabase (altro dominio) e il servizio vocale locale passano diretti.
const CACHE = 'guardian-shell-v1';
self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(['/', '/manifest.webmanifest', '/icona-192.png'])).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', (e) => {
  const r = e.request; const url = new URL(r.url);
  if (r.method !== 'GET' || url.origin !== self.location.origin) return; // dati e API: mai in cache
  if (r.mode === 'navigate') {
    // pagina: prima la rete (versione nuova), senza rete l'ultima shell salvata
    e.respondWith(fetch(r).then((res) => { const copia = res.clone(); caches.open(CACHE).then((c) => c.put('/', copia)); return res; })
      .catch(() => caches.match('/')));
    return;
  }
  if (url.pathname.startsWith('/assets/') || /\.(png|webmanifest)$/.test(url.pathname)) {
    // file con hash nel nome: non cambiano mai, quindi prima la cache
    e.respondWith(caches.match(r).then((c) => c || fetch(r).then((res) => {
      if (res.ok) { const copia = res.clone(); caches.open(CACHE).then((k) => k.put(r, copia)); }
      return res;
    })));
  }
});
