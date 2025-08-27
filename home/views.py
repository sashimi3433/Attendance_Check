from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Q
from datetime import datetime, timedelta
from accounts.models import CustomUser
from attendance_token.models import AttendanceRecord

@login_required
def index(request):
    # キオスクアカウントの場合はチェックインページにリダイレクト
    if request.user.type == 'kiosk':
        return redirect('checkin:qr_scanner')
    # 講師アカウントの場合は講師ダッシュボードにリダイレクト
    elif request.user.type == 'teacher':
        return redirect('teacher_dashboard:index')

    # 生徒アカウントの場合のみホームを表示
    # 現在の日時を取得
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    # ユーザーの出席履歴を取得（最新10件）
    attendance_records = AttendanceRecord.objects.filter(
        user=request.user
    ).order_by('-attended_at')[:10]

    # 全履歴の件数を取得
    total_attendance_count = AttendanceRecord.objects.filter(
        user=request.user
    ).count()

    # 本日の出席状況
    today_attendance = AttendanceRecord.objects.filter(
        user=request.user,
        attended_at__gte=today_start
    ).order_by('-attended_at')

    # 今週の出席回数
    week_attendance_count = AttendanceRecord.objects.filter(
        user=request.user,
        attended_at__gte=week_start
    ).count()

    # 今月の出席回数
    month_attendance_count = AttendanceRecord.objects.filter(
        user=request.user,
        attended_at__gte=month_start
    ).count()

    # 最も利用している場所（上位3つ）
    popular_locations = AttendanceRecord.objects.filter(
        user=request.user
    ).values('location').annotate(
        count=Count('location')
    ).order_by('-count')[:3]

    # 最新の出席記録
    latest_attendance = attendance_records.first() if attendance_records else None

    context = {
        'user': request.user,
        'attendance_records': attendance_records,
        'total_attendance_count': total_attendance_count,
        'show_view_all_link': total_attendance_count > 5,

        # 本日の出席情報
        'today_attendance': today_attendance,
        'today_attendance_count': today_attendance.count(),
        'has_attended_today': today_attendance.exists(),

        # 統計情報
        'week_attendance_count': week_attendance_count,
        'month_attendance_count': month_attendance_count,

        # 人気の場所
        'popular_locations': popular_locations,

        # 最新情報
        'latest_attendance': latest_attendance,

        # 日付情報
        'today': today_start,
        'week_start': week_start,
        'month_start': month_start,
    }
    return render(request, 'home/home.html', context)

@login_required
def account(request):
    # キオスクアカウントの場合はチェックインページにリダイレクト
    if request.user.type == 'kiosk':
        return redirect('checkin:qr_scanner')
    # 講師アカウントの場合は講師ダッシュボードにリダイレクト
    elif request.user.type == 'teacher':
        return redirect('teacher_dashboard:index')
    
    context = {
        'user': request.user,
    }
    return render(request, 'home/home-account.html', context)