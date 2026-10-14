// BUR Slate service worker — release 20261014-174205
// Opens from the phone's copy straight away (works with no signal) and fetches any new release in the background;
// a new release shows the next time the app is opened.
const CACHE = "bur-slate-20261014-174205";
const FILES = ["./", "index.html", "manifest.webmanifest", "icon-192.png", "icon-512.png", "apple-touch-icon.png"];
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  if (e.request.method !== "GET" || new URL(e.request.url).origin !== location.origin) return;
  e.respondWith(caches.open(CACHE).then(async c => {
    const hit = await c.match(e.request, { ignoreSearch: true }) || (e.request.mode === "navigate" ? await c.match("index.html") : undefined);
    // the background fetch goes round every cache (the phone's and GitHub Pages' 10-minute edge cache), so a new release
    // lands on the phone the first time it is opened after the push, not up to ten minutes later (Steve, 13 Oct 2026)
    const fresh = e.request.url + (e.request.url.includes("?") ? "&" : "?") + "u=" + Date.now();
    const net = fetch(fresh, { cache: "no-store" }).then(r => { if (r.ok) c.put(e.request, r.clone()); return r; }).catch(() => hit);
    return hit || net;
  }));
});
