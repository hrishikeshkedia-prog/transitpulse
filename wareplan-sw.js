/* WarePlan Service Worker — offline-first PWA */
const CACHE  = 'wareplan-v1';
const FONTS  = 'wareplan-fonts-v1';

const APP_SHELL = [
  '/wareplan.html',
  '/wareplan-manifest.json',
  '/wareplan-icon-192.png',
  '/wareplan-icon-512.png',
];

// ── Install: cache app shell ──────────────────────────────────────────────────
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(APP_SHELL)).then(() => self.skipWaiting())
  );
});

// ── Activate: purge old caches ────────────────────────────────────────────────
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE && k !== FONTS).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// ── Fetch strategy ────────────────────────────────────────────────────────────
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  // Google Fonts — stale-while-revalidate so offline still works after first load
  if (url.hostname.includes('fonts.goog') || url.hostname.includes('fonts.gstatic')) {
    e.respondWith(
      caches.open(FONTS).then(async cache => {
        const cached = await cache.match(e.request);
        const fetchPromise = fetch(e.request).then(res => {
          if (res.ok) cache.put(e.request, res.clone());
          return res;
        }).catch(() => null);
        return cached || fetchPromise;
      })
    );
    return;
  }

  // App shell — cache-first, network fallback
  if (url.origin === self.location.origin) {
    e.respondWith(
      caches.match(e.request).then(cached => {
        if (cached) return cached;
        return fetch(e.request).then(res => {
          if (res.ok) {
            const clone = res.clone();
            caches.open(CACHE).then(c => c.put(e.request, clone));
          }
          return res;
        }).catch(() => caches.match('/wareplan.html')); // offline fallback
      })
    );
    return;
  }

  // Everything else — network only
  e.respondWith(fetch(e.request));
});
