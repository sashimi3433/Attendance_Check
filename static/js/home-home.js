// static/js/home-home.js

// グローバル変数にトークン情報を格納します
let generatedToken = null;
let tokenExpiresAt = null;
let tokenUsername = null;

document.addEventListener('DOMContentLoaded', async () => {
    // APIのURLはHTMLから取得
    const apiUrl = document.getElementById('generate-token-url').textContent;

    console.log('APIから新しいトークンを取得しようとしています...');

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

        generatedToken = data.token;
        tokenExpiresAt = new Date(data.expires_at);
        tokenUsername = data.username;

        console.log('--- APIからの応答を受信し、トークンが変数に格納されました ---');
        console.log('生成されたトークン:', generatedToken);
        console.log('トークン有効期限:', tokenExpiresAt);
        console.log('トークンユーザー名:', tokenUsername);
        console.log('トークンは使用済みか:', data.is_used);

        JsBarcode("#barcode", generatedToken, {
            format: "code128",
            height:50,
            width:2,
            displayValue: false
        });

        const qrCodeElement = document.getElementById("qrcode");
        const cardElement = qrCodeElement.parentElement;
        const qrCodeSize = cardElement.offsetWidth * 0.25;

        var qrcode = new QRCode(qrCodeElement, {
            text: generatedToken,
            width: qrCodeSize,
            height: qrCodeSize,
            colorDark : "#000000",
            colorLight : "#ffffff",
            correctLevel : QRCode.CorrectLevel.H
        });

    } catch (error) {
        console.error('API呼び出し中にエラーが発生しました:', error);
        generatedToken = null;
        tokenExpiresAt = null;
        tokenUsername = null;
    }
});

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

