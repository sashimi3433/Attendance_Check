from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponseRedirect
import logging

logger = logging.getLogger(__name__)

class UserTypeAccessMiddleware:
    """
    ユーザータイプに基づいてアクセスを制御するミドルウェア
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # ログインしていない場合はスキップ
        if not request.user.is_authenticated:
            return self.get_response(request)

        user_type = request.user.type
        current_path = request.path

        logger.info(f"User {request.user.username} (type: {user_type}) accessing: {current_path}")

        # キオスクアカウントのアクセス制御
        if user_type == 'kiosk':
            # キオスクはQRスキャナーとチェックイン関連のみアクセス可能
            allowed_paths = [
                '/checkin/',
                '/accounts/logout/',
                '/static/',
                '/media/',
            ]
            if not any(current_path.startswith(path) for path in allowed_paths):
                logger.info(f"Redirecting kiosk user to qr_scanner from {current_path}")
                return redirect('checkin:qr_scanner')

        # 講師アカウントのアクセス制御
        elif user_type == 'teacher':
            # 講師は講師ダッシュボードと関連ページのみアクセス可能
            allowed_paths = [
                '/teacher/',
                '/accounts/logout/',
                '/static/',
                '/media/',
            ]
            if not any(current_path.startswith(path) for path in allowed_paths):
                logger.info(f"Redirecting teacher user to teacher_dashboard from {current_path}")
                return redirect('teacher_dashboard:index')

        # 生徒アカウントのアクセス制御
        elif user_type == 'student':
            # 生徒はホームとアカウント関連のみアクセス可能
            allowed_paths = [
                '/',
                '/accounts/',
                '/attendance_token/',
                '/static/',
                '/media/',
            ]
            if not any(current_path.startswith(path) for path in allowed_paths):
                logger.info(f"Redirecting student user to home from {current_path}")
                return redirect('home:index')

        response = self.get_response(request)

        # レスポンスがリダイレクトの場合、そのまま返す（ミドルウェアによる再チェックを防ぐ）
        if isinstance(response, HttpResponseRedirect):
            logger.info(f"Response is redirect, returning as-is: {response['Location']}")
            return response

        return response