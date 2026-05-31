const CACHE_NAME = 'satquest-v1';
const ASSETS = [
  '/sat-prep/',
  '/sat-prep/index.html',
  '/sat-prep/styles.css',
  '/sat-prep/app.js',
  '/sat-prep/manifest.json'
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request))
  );
});

// Handle scheduled notifications
self.addEventListener('notificationclick', e => {
  e.notification.close();
  e.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(clientList => {
      for (const client of clientList) {
        if (client.url.includes('sat-prep') && 'focus' in client) return client.focus();
      }
      if (clients.openWindow) return clients.openWindow('/sat-prep/');
    })
  );
});

// Message handler for scheduling notifications
self.addEventListener('message', e => {
  if (e.data && e.data.type === 'SCHEDULE_NOTIFICATION') {
    const { title, body, delay, tag } = e.data;
    setTimeout(() => {
      self.registration.showNotification(title, {
        body,
        icon: '/sat-prep/icons/icon-192.svg',
        badge: '/sat-prep/icons/icon-72.svg',
        tag: tag || 'satquest',
        requireInteraction: false,
        vibrate: [200, 100, 200]
      });
    }, delay);
  }
});
