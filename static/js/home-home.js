// static/js/home-home.js

// グローバル変数にトークン情報を格納します
let generatedToken = null;
let tokenExpiresAt = null;
let tokenUsername = null;

document.addEventListener('DOMContentLoaded', async () => {
    // APIのURL。myapp/urls.pyとqr_token/urls.pyの設定に合わせてください
    const apiUrl = 'http://localhost:8000/api/generate-token/'; 

    // --- 重要: テスト/開発目的のみです。本番環境では認証情報をハードコードしないでください！ ---
    const testUsername = 'hoge'; // あなたのCustomUserモデルに存在するユーザー名に置き換えてください
    const testPassword = 'hoge'; // そのユーザーのパスワードに置き換えてください
    // --- 重要事項の終わり ---

    console.log('APIから新しいトークンを取得しようとしています...');

    try {
        const response = await fetch(apiUrl, {
            method: 'POST', // ユーザー名とパスワードを送信するためPOSTリクエストを使用
            headers: {
                'Content-Type': 'application/json', // ボディがJSON形式であることを示す
            },
            body: JSON.stringify({ // ユーザー名とパスワードをJSON形式でリクエストボディに含めます
                username: testUsername,
                password: testPassword
            }),
        });

        if (!response.ok) {
            // HTTPステータスコードが200番台以外の場合
            const errorData = await response.json(); // エラーレスポンスもJSONと仮定
            throw new Error(`HTTPエラー! ステータス: ${response.status}, メッセージ: ${errorData.error || '不明なエラー'}`);
        }

        // APIからのJSONレスポンスをパース
        const data = await response.json();

        // 受信したトークンと関連情報をグローバル変数に格納
        generatedToken = data.token; // 'token'という変数名を維持
        tokenExpiresAt = new Date(data.expires_at); // 文字列をDateオブジェクトに変換
        tokenUsername = data.username;

        console.log('--- APIからの応答を受信し、トークンが変数に格納されました ---');
        console.log('生成されたトークン:', generatedToken);
        console.log('トークン有効期限:', tokenExpiresAt);
        console.log('トークンユーザー名:', tokenUsername);
        console.log('トークンは使用済みか:', data.is_used); // 新しいトークンなのでfalseになります

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




        // 必要に応じて、ここで格納した変数を使って他のJavaScript処理を実行できます

    } catch (error) {
        console.error('API呼び出し中にエラーが発生しました:', error);
        // エラー発生時は変数をnullにリセット
        generatedToken = null;
        tokenExpiresAt = null;
        tokenUsername = null;
    }
});

