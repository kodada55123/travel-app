/* 離線快取：進過一次網頁後，民宿收訊再差也能開 */
const CACHE = "party-v2-logistics";
const ASSETS = ["./", "index.html", "style.css", "app.js", "data.js", "logistics.js", "qrcode.js",
  "manifest.webmanifest", "assets/poster.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) =>
      Promise.all(ASSETS.map((a) => c.add(a).catch(() => {}))))  // 海報缺檔也不影響安裝
      .then(() => self.skipWaiting())
  );
});
self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});
// 網路優先、失敗吃快取：平常拿得到最新版，斷線也照常運作
self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET" || !e.request.url.startsWith(self.location.origin)) return;
  e.respondWith(
    fetch(e.request)
      .then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy));
        return res;
      })
      .catch(() => caches.match(e.request, { ignoreSearch: true }))
  );
});
