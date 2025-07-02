# qr_token/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from accounts.models import CustomUser as User # カスタムユーザーモデルの正しいインポートパス
import json
from datetime import datetime, timedelta
import secrets

from .models import QR_Token # 同じアプリ内のモデルをインポート

@csrf_exempt # 警告: 開発・テスト用です。本番環境ではCSRF対策を適切に行ってください。
def token_generator(request): # userid引数は不要になりました
    """
    POSTリクエストでユーザー名とパスワードを受け取り、認証成功時に
    常に新しいQRトークンを生成し、ユーザーに紐付けてDBに保存、JSONで返却するAPI。
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username') # リクエストボディからユーザー名を取得
            password = data.get('password') # リクエストボディからパスワードを取得
        except json.JSONDecodeError:
            return JsonResponse({'error': '不正なJSON形式です'}, status=400)

        user = authenticate(request, username=username, password=password)

        if user is not None:
            # 認証成功
            login(request, user) # オプション: Djangoのセッションにユーザーをログインさせます

            try:
                token = secrets.token_urlsafe(8) # 安全な新しいランダムトークンを生成

                # ユーザーに紐づく新しいQR_Tokenオブジェクトを作成し、データベースに保存
                # これにより、APIが呼び出されるたびに新しいトークンが生成されます
                new_qr_token_instance = QR_Token.objects.create(
                    token=token, # ここで変数名'token'を維持
                    user=user,
                    expires=datetime.now() + timedelta(minutes=5), # 現在時刻から5分後を有効期限に設定
                    is_used=False # 初期状態は未使用
                )

                return JsonResponse({
                    'token': new_qr_token_instance.token, # レスポンスでも'token'というキーを使用
                    'user_id': user.id,
                    'username': user.username,
                    'expires_at': new_qr_token_instance.expires.isoformat(),
                    'is_used': new_qr_token_instance.is_used
                }, status=200)

            except Exception as e:
                # トークン保存時などのデータベースエラーを捕捉
                return JsonResponse({'error': f'トークン生成および保存に失敗しました: {str(e)}'}, status=500)
        else:
            # 認証失敗
            return JsonResponse({'error': 'ユーザー名またはパスワードが無効です'}, status=401)
    else:
        # POST以外のリクエストメソッドは許可しない
        return JsonResponse({'error': 'POSTリクエストのみ許可されています'}, status=405)