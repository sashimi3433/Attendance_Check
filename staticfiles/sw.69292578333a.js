// PWA用のシンプルなService Worker
// オフライン機能は無効化

// Service Worker のインストール
self.addEventListener('install', event => {
  // すぐにアクティブ化
  self.skipWaiting();
});

// Service Worker のアクティベート
self.addEventListener('activate', event => {
  // 既存のキャッシュをクリア
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          return caches.delete(cacheName);
        })
      );
    })
  );
  // すぐにクライアントを制御
  event.waitUntil(clients.claim());
});

// フェッチイベント（ネットワークのみ）
self.addEventListener('fetch', event => {
  // オフライン機能を無効化し、常にネットワークから取得
  event.respondWith(fetch(event.request));
});