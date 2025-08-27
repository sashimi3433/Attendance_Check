from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
from functools import wraps
import csv
import json
import logging

from accounts.models import Kiosk
from attendance_token.models import AttendanceRecord, AttendanceToken
from .models import TeacherDashboardSettings, DashboardStatistics


def teacher_required(view_func):
    """
    講師アカウントのみアクセス可能にするデコレータ
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")

        if request.user.type != "teacher":
            messages.error(request, "講師アカウントでのみアクセス可能です。")
            return redirect("home:index")

        return view_func(request, *args, **kwargs)

    return _wrapped_view


@teacher_required
def dashboard_home(request):
    """
    ダッシュボードホーム画面
    """
    teacher = request.user

    # 基本統計データ
    teacher_kiosks = DashboardStatistics.get_teacher_kiosks(teacher)
    today_attendance = DashboardStatistics.get_today_attendance_count(teacher)
    recent_records = DashboardStatistics.get_recent_attendance_records(teacher, 5)

    # 週間統計
    week_stats = DashboardStatistics.get_attendance_statistics(teacher)

    # 各キオスクに統計情報を追加
    from django.utils import timezone
    from attendance_token.models import AttendanceRecord

    kiosks_with_stats = []
    for kiosk in teacher_kiosks:
        # 今日の出席数を計算
        today = timezone.now().date()
        today_count = AttendanceRecord.objects.filter(
            kiosk=kiosk, attended_at__date=today
        ).count()

        # キオスクオブジェクトに統計情報を追加
        kiosk.today_attendance_count = today_count
        kiosk.active_tokens_count = (
            AttendanceToken.objects.filter(
                attendance_records__kiosk=kiosk,
                is_used=False,
                expires__gt=timezone.now(),
            )
            .distinct()
            .count()
        )
        kiosks_with_stats.append(kiosk)

    # 統計情報をまとめる
    total_active_tokens = (
        AttendanceToken.objects.filter(
            attendance_records__kiosk__in=teacher_kiosks,
            is_used=False,
            expires__gt=timezone.now(),
        )
        .distinct()
        .count()
    )

    stats = {
        "total_kiosks": teacher_kiosks.count(),
        "today_attendance": today_attendance,
        "active_tokens": total_active_tokens,
        "attendance_rate": 85.0,  # TODO: 実際の計算を実装
    }

    context = {
        "stats": stats,
        "kiosks": kiosks_with_stats,
        "recent_attendance": recent_records,
        "teacher_kiosks": teacher_kiosks,
        "kiosk_count": teacher_kiosks.count(),
        "today_attendance": today_attendance,
        "recent_records": recent_records,
        "week_stats": week_stats,
    }

    return render(request, "teacher_dashboard/dashboard_home.html", context)


@teacher_required
def kiosk_management(request):
    """
    キオスク管理画面
    """
    teacher = request.user
    kiosks = Kiosk.objects.filter(teacher=teacher).order_by("name")

    context = {
        "kiosks": kiosks,
    }

    return render(request, "teacher_dashboard/kiosk_management.html", context)


@teacher_required
def kiosk_detail(request, kiosk_id):
    """
    キオスク詳細・設定画面
    """
    teacher = request.user
    kiosk = get_object_or_404(Kiosk, id=kiosk_id, teacher=teacher)

    if request.method == "POST":
        # キオスク設定の更新
        kiosk.name = request.POST.get("name", kiosk.name)
        kiosk.location = request.POST.get("location", kiosk.location)
        new_is_active = request.POST.get("is_active") == "true"

        # 新しく授業の受付を開始する場合、以前の授業の受付を停止
        if new_is_active and not kiosk.is_active:
            # 同じ講師の他のアクティブなキオスクをすべて非アクティブにする
            Kiosk.objects.filter(teacher=kiosk.teacher, is_active=True).exclude(
                id=kiosk.id
            ).update(is_active=False)

        kiosk.is_active = new_is_active
        kiosk.save()

        if new_is_active:
            messages.success(
                request,
                f"キオスク「{kiosk.name}」の授業受付を開始しました。他のキオスクの受付は停止されました。",
            )
        else:
            messages.success(
                request, f"キオスク「{kiosk.name}」の授業受付を停止しました。"
            )
        return redirect("teacher_dashboard:kiosk_detail", kiosk_id=kiosk.id)

    # 今日の日付
    today = timezone.now().date()

    # 統計データの取得
    today_attendance_count = AttendanceRecord.objects.filter(
        kiosk=kiosk, attended_at__date=today
    ).count()

    week_attendance_count = AttendanceRecord.objects.filter(
        kiosk=kiosk, attended_at__date__gte=today - timedelta(days=7)
    ).count()

    total_attendance_count = AttendanceRecord.objects.filter(kiosk=kiosk).count()

    # 今日の出席記録
    today_attendance = (
        AttendanceRecord.objects.filter(kiosk=kiosk, attended_at__date=today)
        .select_related("user")
        .order_by("-attended_at")
    )

    # 週間データの準備（最適化：max_countを一度だけ計算）
    week_data = []
    logging.info(f"Calculating week data for kiosk {kiosk.id}")

    # まず全7日分のカウントを取得
    week_counts = {}
    max_count = 0
    for i in range(7):
        date = today - timedelta(days=6 - i)
        count = AttendanceRecord.objects.filter(
            kiosk=kiosk, attended_at__date=date
        ).count()
        week_counts[date] = count
        max_count = max(max_count, count)
        logging.debug(f"Date {date}: {count} records")

    max_count = max_count or 1

    # データを構築
    for i in range(7):
        date = today - timedelta(days=6 - i)
        count = week_counts[date]
        height = int((count / max_count) * 50) if count > 0 else 5

        week_data.append(
            {
                "date": date,
                "count": count,
                "height": height,
                "day_name": ["月", "火", "水", "木", "金", "土", "日"][date.weekday()],
            }
        )
    logging.info(
        f"Week data calculation completed: {len(week_data)} days, max_count: {max_count}"
    )

    # 有効なトークン（キオスクに関連する未使用の有効なトークンを取得）
    active_tokens = (
        AttendanceToken.objects.filter(
            attendance_records__kiosk=kiosk, is_used=False, expires__gt=timezone.now()
        )
        .distinct()
        .order_by("-created")[:10]
    )  # 最新10件
    logging.info(f"Active tokens for kiosk {kiosk.id}: {len(active_tokens)} tokens")

    # 最近の活動ログ
    recent_activities = (
        AttendanceRecord.objects.filter(kiosk=kiosk)
        .select_related("user")
        .order_by("-attended_at")[:5]
    )

    # 最近の出席記録
    recent_records = (
        AttendanceRecord.objects.filter(kiosk=kiosk)
        .select_related("user")
        .order_by("-attended_at")[:10]
    )

    # 統計データ
    stats = {
        "today_attendance": today_attendance_count,
        "week_attendance": week_attendance_count,
        "active_tokens": len(active_tokens),
        "total_attendance": total_attendance_count,
    }

    context = {
        "kiosk": kiosk,
        "recent_records": recent_records,
        "stats": stats,
        "today": today,
        "today_attendance": today_attendance,
        "week_data": week_data,
        "active_tokens": active_tokens,
        "recent_activities": recent_activities,
    }

    return render(request, "teacher_dashboard/kiosk_detail.html", context)


@teacher_required
def attendance_history(request):
    """
    出席履歴画面
    """
    teacher = request.user
    teacher_kiosks = DashboardStatistics.get_teacher_kiosks(teacher)

    # フィルタリング
    records = (
        AttendanceRecord.objects.filter(kiosk__in=teacher_kiosks)
        .select_related("user", "kiosk")
        .order_by("-attended_at")
    )

    # 検索・フィルタ処理
    search_query = request.GET.get("search", "")
    kiosk_filter = request.GET.get("kiosk", "")
    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")

    if search_query:
        records = records.filter(
            Q(user__username__icontains=search_query)
            | Q(user__name__icontains=search_query)
        )

    if kiosk_filter:
        records = records.filter(kiosk_id=kiosk_filter)

    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
            records = records.filter(attended_at__date__gte=date_from_obj)
            logging.info(f"Applied date_from filter: {date_from_obj}")
        except ValueError as e:
            logging.error(f"Invalid date_from format: {date_from}, error: {e}")

    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
            records = records.filter(attended_at__date__lte=date_to_obj)
            logging.info(f"Applied date_to filter: {date_to_obj}")
        except ValueError as e:
            logging.error(f"Invalid date_to format: {date_to}, error: {e}")

    # ページネーション
    paginator = Paginator(records, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "teacher_kiosks": teacher_kiosks,
        "search_query": search_query,
        "kiosk_filter": kiosk_filter,
        "date_from": date_from,
        "date_to": date_to,
    }

    return render(request, "teacher_dashboard/attendance_history.html", context)


@teacher_required
def attendance_export(request):
    """
    出席履歴CSV出力
    """
    teacher = request.user
    teacher_kiosks = DashboardStatistics.get_teacher_kiosks(teacher)

    # 同じフィルタリング条件を適用
    records = (
        AttendanceRecord.objects.filter(kiosk__in=teacher_kiosks)
        .select_related("user", "kiosk")
        .order_by("-attended_at")
    )

    # フィルタ適用（attendance_historyと同じロジック）
    search_query = request.GET.get("search", "")
    kiosk_filter = request.GET.get("kiosk", "")
    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")

    if search_query:
        records = records.filter(
            Q(user__username__icontains=search_query)
            | Q(user__name__icontains=search_query)
        )

    if kiosk_filter:
        records = records.filter(kiosk_id=kiosk_filter)

    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
            records = records.filter(attended_at__date__gte=date_from_obj)
            logging.info(f"Export: Applied date_from filter: {date_from_obj}")
        except ValueError as e:
            logging.error(f"Export: Invalid date_from format: {date_from}, error: {e}")

    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
            records = records.filter(attended_at__date__lte=date_to_obj)
            logging.info(f"Export: Applied date_to filter: {date_to_obj}")
        except ValueError as e:
            logging.error(f"Export: Invalid date_to format: {date_to}, error: {e}")

    # CSV出力
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="attendance_records_{timezone.now().strftime("%Y%m%d")}.csv"'
    )
    response.write("\ufeff")  # BOM for Excel

    writer = csv.writer(response)
    writer.writerow(["出席日時", "生徒名", "ユーザー名", "キオスク名", "設置場所"])

    for record in records:
        writer.writerow(
            [
                record.attended_at.strftime("%Y-%m-%d %H:%M:%S"),
                record.user.name or "",
                record.user.username,
                record.kiosk.name,
                record.kiosk.location,
            ]
        )

    return response


@teacher_required
def statistics_analysis(request):
    """
    統計・分析画面
    """
    teacher = request.user

    # 期間設定（デフォルトは過去30日）
    period_days = int(request.GET.get("period", 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=period_days)

    # 統計データ取得
    stats = DashboardStatistics.get_attendance_statistics(teacher, start_date, end_date)

    # キオスク別統計
    teacher_kiosks = DashboardStatistics.get_teacher_kiosks(teacher)
    kiosk_stats = []
    for kiosk in teacher_kiosks:
        kiosk_records = AttendanceRecord.objects.filter(
            kiosk=kiosk, attended_at__date__range=[start_date, end_date]
        ).count()
        kiosk_stats.append({"kiosk": kiosk, "count": kiosk_records})

    # デフォルト日付の設定（フォーム用）
    default_date_from = start_date.strftime("%Y-%m-%d")
    default_date_to = end_date.strftime("%Y-%m-%d")

    # グラフ用データの準備
    import json

    daily_stats = stats.get("daily_stats", {})
    daily_labels = json.dumps(list(daily_stats.keys()))
    daily_data = json.dumps(list(daily_stats.values()))

    # 時間帯別データ（仮のデータ）
    hourly_labels = json.dumps(
        ["9:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00"]
    )
    hourly_data = json.dumps(
        [0, 0, 0, 0, 0, 0, 0, 0, 0]
    )  # 実際のデータに置き換える必要がある

    # キオスク別データ
    kiosk_labels = json.dumps([stat["kiosk"].name for stat in kiosk_stats])
    kiosk_data = json.dumps([stat["count"] for stat in kiosk_stats])

    context = {
        "stats": stats,
        "kiosk_stats": kiosk_stats,
        "period_days": period_days,
        "start_date": start_date,
        "end_date": end_date,
        "default_date_from": default_date_from,
        "default_date_to": default_date_to,
        "teacher_kiosks": teacher_kiosks,
        "daily_labels": daily_labels,
        "daily_data": daily_data,
        "hourly_labels": hourly_labels,
        "hourly_data": hourly_data,
        "kiosk_labels": kiosk_labels,
        "kiosk_data": kiosk_data,
    }

    return render(request, "teacher_dashboard/statistics_analysis.html", context)


@teacher_required
def statistics_api(request):
    """
    統計データAPI（グラフ用）
    """
    teacher = request.user

    period_days = int(request.GET.get("period", 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=period_days)

    stats = DashboardStatistics.get_attendance_statistics(teacher, start_date, end_date)

    return JsonResponse(stats)


@teacher_required
def dashboard_stats_api(request):
    """
    ダッシュボード統計データAPI（リアルタイム更新用）
    """
    teacher = request.user

    # 基本統計データ
    teacher_kiosks = DashboardStatistics.get_teacher_kiosks(teacher)
    today_attendance = DashboardStatistics.get_today_attendance_count(teacher)
    recent_records = DashboardStatistics.get_recent_attendance_records(teacher, 5)

    # 週間統計
    week_stats = DashboardStatistics.get_attendance_statistics(teacher)

    # アクティブなトークン数を計算
    active_tokens = (
        AttendanceToken.objects.filter(
            attendance_records__kiosk__in=teacher_kiosks,
            is_used=False,
            expires__gt=timezone.now(),
        )
        .distinct()
        .count()
    )

    # レスポンスデータ
    response_data = {
        "stats": {
            "total_kiosks": len(teacher_kiosks),
            "today_attendance": today_attendance,
            "active_tokens": active_tokens,
            "weekly_attendance": week_stats.get("total_attendance", 0),
        },
        "recent_attendance": [
            {
                "timestamp": record.attended_at.strftime("%H:%M"),
                "user_name": record.user.name
                if hasattr(record.user, "name") and record.user.name
                else record.user.username,
                "kiosk_name": record.kiosk.name,
            }
            for record in recent_records
        ],
    }

    return JsonResponse(response_data)


@teacher_required
def settings_view(request):
    """
    設定画面
    """
    teacher = request.user

    # 設定オブジェクトを取得または作成
    settings, created = TeacherDashboardSettings.objects.get_or_create(teacher=teacher)

    if request.method == "POST":
        # 設定の更新
        settings.email_notifications = request.POST.get("email_notifications") == "on"
        settings.daily_report = request.POST.get("daily_report") == "on"
        settings.weekly_report = request.POST.get("weekly_report") == "on"
        settings.records_per_page = int(request.POST.get("records_per_page", 20))
        settings.default_period_days = int(request.POST.get("default_period_days", 7))
        settings.save()

        messages.success(request, "設定を更新しました。")
        return redirect("teacher_dashboard:settings")

    context = {
        "settings": settings,
    }

    return render(request, "teacher_dashboard/settings.html", context)
