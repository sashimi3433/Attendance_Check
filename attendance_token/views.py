# attendance_token/views.py
# 出席管理用トークン生成ビュー
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from accounts.models import CustomUser as User
import json
from datetime import timedelta
import secrets

from .models import AttendanceToken, AttendanceRecord
from .utils import get_client_ip, log_ip_access

@csrf_exempt
@login_required
def token_generator(request):
    """
    出席確認用のトークンを生成するAPI
    ユーザーがQRコードまたはバーコードで出席確認を行うためのトークンを作成
    """
    if request.method == 'POST':
        user = request.user
        try:
            # 出席確認用の8文字のセキュアなトークンを生成
            token = secrets.token_urlsafe(8)
            
            # クライアントのIPアドレスを取得
            client_ip = get_client_ip(request)
            
            # 新しい出席確認トークンをデータベースに保存
            new_attendance_token_instance = AttendanceToken.objects.create(
                token=token,
                user=user,
                expires=timezone.now() + timedelta(seconds=5),  # 5秒間有効
                is_used=False,  # 初期状態は未使用
                issued_ip=client_ip  # 発行元IPアドレスを記録
            )
            
            # IPアクセスをログに記録
            log_ip_access(request, "token_generation", f"Token: {token[:8]}...")
            # 生成されたトークン情報をJSONで返却
            return JsonResponse({
                'token': new_attendance_token_instance.token,
                'user_id': user.id,
                'username': user.username,
                'expires_at': new_attendance_token_instance.expires.isoformat(),
                'is_used': new_attendance_token_instance.is_used
            }, status=200)
        except Exception as e:
            return JsonResponse({'error': f'出席確認トークンの生成に失敗しました: {str(e)}'}, status=500)
    else:
        return JsonResponse({'error': 'POSTリクエストのみ許可されています'}, status=405)





@login_required
def get_attendance_history(request):
    """
    ユーザーの出席履歴を取得するAPI
    """
    if request.method == 'GET':
        try:
            # ユーザーの出席記録を取得（最新10件）
            attendance_records = AttendanceRecord.objects.filter(
                user=request.user
            ).order_by('-attended_at')[:10]
            
            records_data = []
            for record in attendance_records:
                records_data.append({
                    'id': record.id,
                    'attended_at': record.attended_at.strftime('%Y/%m/%d %H:%M'),
                    'location': record.location or '未指定',
                    'notes': record.notes or ''
                })
            
            return JsonResponse({
                'attendance_history': records_data,
                'total_count': AttendanceRecord.objects.filter(user=request.user).count()
            }, status=200)
            
        except Exception as e:
            return JsonResponse({'error': f'出席履歴の取得でエラーが発生しました: {str(e)}'}, status=500)
    else:
        return JsonResponse({'error': 'GETリクエストのみ許可されています'}, status=405)




@login_required
def attendance_detail(request, record_id):
    """
    出席記録の詳細を表示
    """
    try:
        # ユーザー自身の出席記録のみ取得可能
        record = AttendanceRecord.objects.select_related(
            'lesson__teacher__user', 'lesson'
        ).get(
            id=record_id,
            user=request.user
        )
        
        # 担当講師名を取得
        teacher_name = ""
        if record.lesson and record.lesson.teacher:
            teacher_name = record.lesson.teacher.user.name or record.lesson.teacher.user.username
        
        # キオスク名を取得（レッスンの場所に基づいて）
        kiosk_name = ""
        if record.lesson and record.lesson.location:
            from accounts.models import Kiosk
            try:
                kiosk = Kiosk.objects.get(location=record.lesson.location)
                kiosk_name = kiosk.user.name or kiosk.user.username
            except Kiosk.DoesNotExist:
                kiosk_name = record.lesson.location  # キオスクが見つからない場合は場所名を表示
        
        context = {
            'record': record,
            'teacher_name': teacher_name,
            'kiosk_name': kiosk_name
        }
        
        return render(request, 'attendance_token/attendance_detail.html', context)
        
    except AttendanceRecord.DoesNotExist:
        return render(request, 'attendance_token/error.html', {
            'error_message': '指定された出席記録が見つかりません。'
        })