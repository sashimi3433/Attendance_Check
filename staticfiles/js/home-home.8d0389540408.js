// static/js/home-home.js
// 出席管理用QRコード生成スクリプト

// グローバル変数に出席確認トークン情報を格納します
let attendanceToken = null;
let tokenExpiresAt = null;
let tokenUsername = null;
let countdownInterval = null;
let qrCodeInstance = null;

document.addEventListener('DOMContentLoaded', async () => {
    // APIのURLはHTMLから取得
    const apiUrl = document.getElementById('generate-token-url').textContent;

    console.log('出席確認用の新しいトークンを取得しようとしています...');

    try {
        const response = await fetch(apiUrl, {
            method: 'POST', // POSTリクエストを維持
            headers: {
                'Content-Type': 'application/json',
                // CSRFトークンをヘッダーに追加
                'X-CSRFToken': getCookie('csrftoken'),
            },
            // ボディは空にする
            body: JSON.stringify({}),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`HTTPエラー! ステータス: ${response.status}, メッセージ: ${errorData.error || '不明なエラー'}`);
        }

        const data = await response.json();

        attendanceToken = data.token;
        tokenExpiresAt = new Date(data.expires_at);
        tokenUsername = data.username;

        console.log('--- 出席確認用トークンが正常に生成されました ---');
        console.log('出席確認トークン:', attendanceToken);
        console.log('トークン有効期限:', tokenExpiresAt);
        console.log('ユーザー名:', tokenUsername);
        console.log('トークン使用状況:', data.is_used ? '使用済み' : '未使用');

        // QRコードとバーコードを生成
        generateQRCodeAndBarcode();
        
        // カウントダウンタイマーを開始
        startCountdownTimer();
        
        // トークンステータスを更新
        updateTokenStatus('active');

    } catch (error) {
        console.error('出席確認トークンの取得中にエラーが発生しました:', error);
        attendanceToken = null;
        tokenExpiresAt = null;
        tokenUsername = null;
        updateTokenStatus('error');
        stopCountdownTimer();
    }

    // 出席確認ボタンのイベントリスナーを追加
    const attendanceBtn = document.getElementById('attendance-btn');
    if (attendanceBtn) {
        attendanceBtn.addEventListener('click', handleAttendanceCheck);
    }
});

// 出席確認処理
function handleAttendanceCheck() {
    if (!attendanceToken) {
        alert('出席確認用のQRコードを先に生成してください。');
        return;
    }
    
    // 出席確認APIを呼び出し
    fetch('/attendance_token/confirm-attendance/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            token: attendanceToken,
            location: '教室A' // 固定値、必要に応じて動的に変更可能
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            alert(data.message);
            // 出席確認後にページをリロードして履歴を更新
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else if (data.error) {
            alert('エラー: ' + data.error);
        }
    })
    .catch(error => {
        console.error('出席確認エラー:', error);
        alert('出席確認処理でエラーが発生しました。');
    });
}

// CSRFトークンを取得する関数
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// すべての履歴を表示/非表示を切り替える関数
function toggleAllHistory() {
    const allHistoryList = document.querySelector('.all-history');
    const viewAllLink = document.querySelector('.view-all-link');
    
    if (!allHistoryList || !viewAllLink) return;
    
    const isHidden = allHistoryList.style.display === 'none';
    
    if (isHidden) {
        allHistoryList.style.display = 'block';
        viewAllLink.textContent = '履歴を折りたたむ';
    } else {
        allHistoryList.style.display = 'none';
        viewAllLink.textContent = 'すべての履歴を表示';
    }
}

// CSRFトークンを取得するためのヘルパー関数
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// QRコードとバーコードを生成する関数
function generateQRCodeAndBarcode() {
    if (!attendanceToken) return;
    
    // 既存のQRコードをクリア
    const qrCodeElement = document.getElementById("qrcode");
    qrCodeElement.innerHTML = '';
    
    // 出席確認用バーコード生成
    JsBarcode("#barcode", attendanceToken, {
        format: "code128",
        height: 50,
        width: 2,
        displayValue: false
    });
    
    // QRコードサイズを計算
    const cardElement = qrCodeElement.parentElement;
    const qrCodeSize = cardElement.offsetWidth * 0.35;
    
    // 出席確認用QRコード生成
    qrCodeInstance = new QRCode(qrCodeElement, {
        text: attendanceToken,
        width: qrCodeSize,
        height: qrCodeSize,
        colorDark: "#000000",
        colorLight: "#ffffff",
        correctLevel: QRCode.CorrectLevel.H
    });
}

// カウントダウンタイマーを開始する関数
function startCountdownTimer() {
    // 既存のタイマーを停止
    stopCountdownTimer();
    
    if (!tokenExpiresAt) return;
    
    countdownInterval = setInterval(() => {
        const now = new Date();
        const timeLeft = tokenExpiresAt - now;
        
        if (timeLeft <= 0) {
            // 期限切れ時の処理
            handleTokenExpired();
            return;
        }
        
        // 残り時間を表示
        const minutes = Math.floor(timeLeft / 60000);
        const seconds = Math.floor((timeLeft % 60000) / 1000);
        const formattedTime = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        const timerElement = document.getElementById('countdown-timer');
        if (timerElement) {
            timerElement.textContent = formattedTime;
            
            // 残り時間に応じてスタイルを変更
            timerElement.classList.remove('warning', 'expired');
            if (timeLeft <= 60000) { // 1分以下
                timerElement.classList.add('warning');
            }
        }
    }, 1000);
}

// カウントダウンタイマーを停止する関数
function stopCountdownTimer() {
    if (countdownInterval) {
        clearInterval(countdownInterval);
        countdownInterval = null;
    }
}

// トークンが期限切れになった時の処理
function handleTokenExpired() {
    console.log('トークンが期限切れになりました。新しいトークンを生成します...');
    
    // タイマーを停止
    stopCountdownTimer();
    
    // 期限切れ表示
    const timerElement = document.getElementById('countdown-timer');
    if (timerElement) {
        timerElement.textContent = '期限切れ';
        timerElement.classList.add('expired');
    }
    
    updateTokenStatus('updating');
    
    // 新しいトークンを自動生成
    generateNewToken();
}

// 新しいトークンを生成する関数
async function generateNewToken() {
    try {
        const apiUrl = document.getElementById('generate-token-url').textContent;
        
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({}),
        });
        
        if (!response.ok) {
            throw new Error(`HTTPエラー! ステータス: ${response.status}`);
        }
        
        const data = await response.json();
        
        // グローバル変数を更新
        attendanceToken = data.token;
        tokenExpiresAt = new Date(data.expires_at);
        tokenUsername = data.username;
        
        console.log('新しいトークンが生成されました:', attendanceToken);
        
        // QRコードとバーコードを再生成
        generateQRCodeAndBarcode();
        
        // カウントダウンタイマーを再開
        startCountdownTimer();
        
        // ステータスを更新
        updateTokenStatus('active');
        
    } catch (error) {
        console.error('新しいトークンの生成中にエラーが発生しました:', error);
        updateTokenStatus('error');
    }
}

// トークンステータスを更新する関数
function updateTokenStatus(status) {
    const statusElement = document.getElementById('token-status');
    if (!statusElement) return;
    
    // 既存のクラスを削除
    statusElement.classList.remove('active', 'expired', 'updating', 'error');
    
    switch (status) {
        case 'active':
            statusElement.textContent = 'トークン有効';
            statusElement.classList.add('active');
            break;
        case 'expired':
            statusElement.textContent = 'トークン期限切れ';
            statusElement.classList.add('expired');
            break;
        case 'updating':
            statusElement.textContent = 'トークン更新中...';
            statusElement.classList.add('updating');
            break;
        case 'error':
            statusElement.textContent = 'トークン生成エラー';
            statusElement.classList.add('error');
            break;
        default:
            statusElement.textContent = 'トークン生成中...';
    }
}

