// PWA機能の初期化
(function() {
  'use strict';

  // Service Workerの登録
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/static/sw.js')
        .then((registration) => {
          console.log('Service Worker: 登録成功', registration.scope);
        })
        .catch((error) => {
          console.log('Service Worker: 登録失敗', error);
        });
    });
  }

  // インストールプロンプトの処理
  let deferredPrompt;
  const installButton = document.getElementById('install-button');

  window.addEventListener('beforeinstallprompt', (event) => {
    console.log('PWA: インストールプロンプトが表示可能です');
    // デフォルトのプロンプトを防ぐ
    event.preventDefault();
    // 後で使用するためにイベントを保存
    deferredPrompt = event;
    
    // インストールボタンを表示（存在する場合）
    if (installButton) {
      installButton.style.display = 'block';
    }
  });

  // インストールボタンのクリック処理
  if (installButton) {
    installButton.addEventListener('click', () => {
      if (deferredPrompt) {
        // インストールプロンプトを表示
        deferredPrompt.prompt();
        
        // ユーザーの選択結果を処理
        deferredPrompt.userChoice.then((choiceResult) => {
          if (choiceResult.outcome === 'accepted') {
            console.log('PWA: ユーザーがインストールを承認しました');
          } else {
            console.log('PWA: ユーザーがインストールを拒否しました');
          }
          deferredPrompt = null;
          installButton.style.display = 'none';
        });
      }
    });
  }

  // アプリがインストールされた時の処理
  window.addEventListener('appinstalled', () => {
    console.log('PWA: アプリがインストールされました');
    if (installButton) {
      installButton.style.display = 'none';
    }
  });

  // オフライン機能は無効化されているため、オンライン状態監視は削除
})();