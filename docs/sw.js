// =====================================================================
// デジトレ PWA版：Service Worker（オフライン対応の裏方）
//
// Service Worker は「ページとネットの間に立つ配達員」のような仕組み。
// 初回に部品一式（HTML/CSS/JS/アイコン）を端末のキャッシュ（＝保存庫）に
// しまっておき、次からはネットに行かずキャッシュから渡す。
// → 電波が無くても、ホーム画面のアイコンからアプリを開けるようになる。
//
// ★アプリのファイルを更新したら、下の CACHE_NAME の番号を上げること。
//   名前が変わると「古い保存庫を捨てて新しく取り直す」動きになる。
// =====================================================================

const CACHE_NAME = "digitore-v1";

// 端末に保存しておく部品の一覧（このアプリを動かすのに必要な全ファイル）
const ASSETS = [
  "./",
  "./index.html",
  "./style.css",
  "./app.js",
  "./foods.js",
  "./targets.js",
  "./intake.js",
  "./consult.js",
  "./safety.js",
  "./storage.js",
  "./charts.js",
  "./vendor/chart.umd.js",
  "./manifest.webmanifest",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/apple-touch-icon.png",
];

// 【取り付け時】部品一式をキャッシュにしまう
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(ASSETS))
      .then(() => self.skipWaiting()) // 待たずに新しい配達員へ交代する
  );
});

// 【交代時】古い名前のキャッシュ（前のバージョンの保存庫）を掃除する
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((names) => Promise.all(
        names.filter((n) => n !== CACHE_NAME).map((n) => caches.delete(n))
      ))
      .then(() => self.clients.claim()) // いま開いている画面もすぐ担当する
  );
});

// 【毎回の配達】まずキャッシュを見て、あればそれを返す。無ければネットへ。
// （＝キャッシュ優先。オフラインでも動くことをいちばん大事にする方針）
self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request).catch(() => {
        // ネットも使えない場合：画面の移動（ページ表示）なら本体HTMLで代用する
        if (event.request.mode === "navigate") {
          return caches.match("./index.html");
        }
      });
    })
  );
});
