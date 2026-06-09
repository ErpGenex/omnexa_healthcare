/* Omnexa Healthcare PWA — offline shell cache */
const CACHE = "omnexa-healthcare-v1";
const ASSETS = [
	"/assets/omnexa_healthcare/css/healthcare-rtl.css",
	"/assets/frappe/dist/css/desk.bundle.css",
];

self.addEventListener("install", (event) => {
	event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(ASSETS)));
	self.skipWaiting();
});

self.addEventListener("fetch", (event) => {
	if (event.request.method !== "GET") return;
	event.respondWith(
		caches.match(event.request).then((cached) => cached || fetch(event.request))
	);
});
