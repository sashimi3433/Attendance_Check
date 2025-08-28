# checkin/views.py
# チェックイン機能専用ビュー
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone
from accounts.models import CustomUser as User, Lesson
from accounts.views import user_type_required
from attendance_token.models import AttendanceToken, AttendanceRecord
from attendance_token.utils import get_client_ip, log_ip_access
import json






@user_type_required('kiosk')
def success_page(request):
    """
    出席確認成功ページを表示
    """
    return render(request, 'checkin/success.html')


@user_type_required('kiosk')
def error_page(request):
    """
    出席確認エラーページを表示
    """
    return render(request, 'checkin/error.html')


@user_type_required('kiosk')
def qr_scanner(request):
    """
    QRスキャナーページを表示
    キオスクアカウントのみアクセス可能
    """
    current_lesson = Lesson.objects.filter(location=request.user.name, reception=True).first()
    return render(request, 'checkin/qr_scanner.html', {'current_lesson': current_lesson})


@csrf_exempt
@user_type_required('kiosk')
def confirm_attendance(request):
    """
    出席確認処理
    QRスキャナーからのPOSTリクエストを処理し、トークン検証と出席記録を作成
    """
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'POSTメソッドのみ許可されています'
        }, status=405)
    
    try:
        # リクエストボディからJSONデータを取得
        data = json.loads(request.body)
        token_value = data.get('token', '').strip()
        status = data.get('status', 'present')
        
        # 必須パラメータの検証
        if not token_value:
            return JsonResponse({
                'success': False,
                'error': 'トークンが指定されていません'
            }, status=400)
        
        # トークンの検証とユーザーの特定
        try:
            attendance_token = AttendanceToken.objects.get(
                token=token_value,
                is_used=False
            )
            # トークンからユーザーを取得
            user = attendance_token.user
        except AttendanceToken.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'トークンが無効または既に使用済みです'
            }, status=400)
        
        # トークンの有効期限確認
        if attendance_token.is_expired():
            return JsonResponse({
                'success': False,
                'error': 'トークンの有効期限が切れています'
            }, status=400)
        
        # IPアドレス制限チェック
        current_ip = get_client_ip(request)
        if attendance_token.issued_ip and attendance_token.issued_ip != current_ip:
            # IPアドレス不一致をログに記録
            log_ip_access(
                request, 
                "checkin_ip_mismatch", 
                f"Token IP: {attendance_token.issued_ip}, Current IP: {current_ip}, User: {user.username}"
            )
            return JsonResponse({
                'success': False,
                'error': 'IPアドレスが一致しません。トークンを発行した端末と同じ端末からアクセスしてください。'
            }, status=403)
        
        # 既に同じトークンで出席記録が存在するかチェック
        existing_record = AttendanceRecord.objects.filter(
            user=user,
            token=attendance_token
        ).first()
        
        if existing_record:
            return JsonResponse({
                'success': False,
                'error': '既にこのトークンで出席確認済みです'
            }, status=400)
        
        # 現在のレッスンを取得
        current_lesson = None
        if hasattr(request.user, 'kiosk_profile') and request.user.kiosk_profile.current_lesson:
            current_lesson = request.user.kiosk_profile.current_lesson

        # アクティブなレッスンの検証
        if not current_lesson or not current_lesson.is_active:
            return JsonResponse({
                'success': False,
                'error': 'アクティブなレッスンがありません。チェックインは許可されていません。'
            }, status=400)

        # 出席記録の作成
        attendance_record = AttendanceRecord.objects.create(
            user=user,
            token=attendance_token,
            lesson=current_lesson,
            status=status,
            location=data.get('location', ''),
            notes=f'キオスクからの出席確認 - {timezone.now().strftime("%Y/%m/%d %H:%M:%S")}'
        )
        
        # トークンを使用済みにマーク
        attendance_token.mark_as_used()
        
        # 成功時のIPアクセスをログに記録
        log_ip_access(
            request, 
            "checkin_success", 
            f"User: {user.username}, Token: {token_value[:8]}..., IP: {current_ip}"
        )
        
        return JsonResponse({
            'success': True,
            'message': '出席確認が完了しました',
            'data': {
                'user': user.username,
                'status': attendance_record.status,
                'attended_at': attendance_record.attended_at.strftime('%Y/%m/%d %H:%M:%S'),
                'record_id': attendance_record.id
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': '無効なJSONデータです'
        }, status=400)
    
    except Exception as e:
        # 予期しないエラーのログ記録（本番環境では適切なログシステムを使用）
        print(f"出席確認エラー: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'サーバー内部エラーが発生しました'
        }, status=500)
