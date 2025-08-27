# checkin/views.py
# チェックイン機能専用ビュー
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from accounts.models import CustomUser as User, Kiosk
from attendance_token.models import AttendanceToken, AttendanceRecord
import json


@csrf_exempt
@login_required
def confirm_attendance(request):
    """
    出席確認を行うAPI（kioskアカウントのみ実行可能）
    QRコードまたはバーコードから読み取ったトークンで出席を記録
    """
    if request.method == 'POST':
        # kioskアカウントのみ出席確認を実行可能
        if request.user.type != 'kiosk':
            return JsonResponse({'error': 'QRコード読み取り機能はキオスク端末のみ利用可能です。'}, status=403)
        
        try:
            # キオスク情報を取得
            try:
                kiosk = Kiosk.objects.get(user=request.user)
            except Kiosk.DoesNotExist:
                return JsonResponse({'error': 'キオスク情報が見つかりません。'}, status=404)
            
            data = json.loads(request.body)
            token_value = data.get('token')
            status = data.get('status', 'present')  # デフォルトは出席
            location = data.get('location', kiosk.location)  # デフォルトはキオスクの設置場所

            if not token_value:
                return JsonResponse({'error': 'トークンが指定されていません'}, status=400)
            
            # トークンの存在確認
            try:
                attendance_token = AttendanceToken.objects.get(token=token_value)
            except AttendanceToken.DoesNotExist:
                return JsonResponse({'error': '無効なトークンです'}, status=404)
            
            # トークンの有効期限チェック
            if attendance_token.is_expired():
                return JsonResponse({'error': 'トークンの有効期限が切れています'}, status=400)
            
            # トークンの使用済みチェック
            if attendance_token.is_used:
                return JsonResponse({'error': 'このトークンは既に使用済みです'}, status=400)
            
            # 重複出席チェック（同じトークンでの重複確認を防ぐ）
            existing_record = AttendanceRecord.objects.filter(
                user=attendance_token.user,
                token=attendance_token
            ).first()
            
            if existing_record:
                return JsonResponse({'error': '既にこのトークンで出席確認済みです'}, status=400)
            
            # 出席記録を作成（トークンの所有者の出席を記録）
            attendance_record = AttendanceRecord.objects.create(
                user=attendance_token.user,  # トークンの所有者
                token=attendance_token,
                kiosk=kiosk,  # 読み取りを行ったキオスク
                location=location,
                status=status
            )
            
            # トークンを使用済みにマーク
            attendance_token.mark_as_used()
            
            return JsonResponse({
                'message': '出席確認が完了しました',
                'attendance_id': attendance_record.id,
                'attended_at': attendance_record.attended_at.isoformat(),
                'location': attendance_record.location,
                'user': attendance_token.user.username,
                'kiosk': kiosk.name
            }, status=200)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': '無効なJSONデータです'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'出席確認処理でエラーが発生しました: {str(e)}'}, status=500)
    else:
        return JsonResponse({'error': 'POSTリクエストのみ許可されています'}, status=405)


@login_required
def qr_scanner(request):
    """
    QRコード読み取りページを表示（kioskアカウントのみアクセス可能）
    """
    # kioskアカウントのみアクセス可能
    if request.user.type != 'kiosk':
        return render(request, 'checkin/error.html', {
            'error_message': 'QRコード読み取り機能はキオスク端末のみ利用可能です。'
        })
    
    # キオスク情報を取得
    try:
        kiosk = Kiosk.objects.get(user=request.user)
        teacher_name = kiosk.teacher.name if kiosk.teacher else None
    except Kiosk.DoesNotExist:
        teacher_name = None
    
    return render(request, 'checkin/qr_scanner.html', {
        'teacher_name': teacher_name
    })


@login_required
def success_page(request):
    """
    出席確認成功ページを表示
    """
    return render(request, 'checkin/success.html')


@login_required
def error_page(request):
    """
    出席確認エラーページを表示
    """
    return render(request, 'checkin/error.html')
