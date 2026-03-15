const CACHE = 'captains-log-v2';
const ASSETS = [
  '/',
  '/index.html',
  '/subanshu-dashboard.html',
  '/training-hub.html',
  '/manifest.json',
  '/icon-192.svg',
  '/icon-512.svg',
  '/icon-maskable.svg',
];

// Install — cache all static assets
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(cache => cache.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});

// Activate — clean up old caches
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// Fetch — stale-while-revalidate for HTML/assets, network-first for Firebase
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  // Let Firebase & Google APIs go straight to network
  if (url.hostname.includes('firebase') ||
      url.hostname.includes('googleapis') ||
      url.hostname.includes('gstatic') ||
      url.hostname.includes('firestore')) {
    return;
  }

  // For our own assets: serve from cache, update in background
  e.respondWith(
    caches.open(CACHE).then(cache =>
      cache.match(e.request).then(cached => {
        const fresh = fetch(e.request).then(res => {
          if (res.ok) cache.put(e.request, res.clone());
          return res;
        }).catch(() => cached);
        return cached || fresh;
      })
    )
  );
});
