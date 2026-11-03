/* Only the app shell. Never cache API responses, provider data or media segments. */
const CACHE='magforgelab-shell-v15';
const SHELL=['/tv/track-controls.js?v=1','/tv/track-controls.css?v=1','/web/','/web/app.css?v=15','/web/app.js?v=15','/web/vendor/hls.min.js','/web/icon-192.png','/web/icon-512.png','/assets/media-forge-lab.png','/assets/tv.png','/assets/movie.png','/assets/series.png','/assets/all.png','/assets/episode.png'];
self.addEventListener('install',event=>event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(SHELL)).then(()=>self.skipWaiting())));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('magforgelab-shell-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',event=>{const u=new URL(event.request.url);if(event.request.method!=='GET'||u.origin!==self.location.origin||!SHELL.includes(u.pathname+u.search))return;event.respondWith(fetch(event.request).catch(()=>caches.match(event.request)));});
