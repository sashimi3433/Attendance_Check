# qr_token/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from accounts.models import CustomUser as User
import json
from datetime import datetime, timedelta
import secrets

from .models import QR_Token

@csrf_exempt
@login_required
def token_generator(request):
    if request.method == 'POST':
        user = request.user
        try:
            token = secrets.token_urlsafe(8)
            new_qr_token_instance = QR_Token.objects.create(
                token=token,
                user=user,
                expires=datetime.now() + timedelta(minutes=5),
                is_used=False
            )
            return JsonResponse({
                'token': new_qr_token_instance.token,
                'user_id': user.id,
                'username': user.username,
                'expires_at': new_qr_token_instance.expires.isoformat(),
                'is_used': new_qr_token_instance.is_used
            }, status=200)
        except Exception as e:
            return JsonResponse({'error': f'トークン生成および保存に失敗しました: {str(e)}'}, status=500)
    else:
        return JsonResponse({'error': 'POSTリクエストのみ許可されています'}, status=405)