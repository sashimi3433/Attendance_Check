from django.db import models
from django.contrib.auth import get_user_model
from accounts.models import Kiosk
from attendance_token.models import AttendanceRecord
from django.utils import timezone
from datetime import datetime, timedelta

User = get_user_model()

class TeacherDashboardSettings(models.Model):
    """
    講師ダッシュボードの個人設定モデル
    """
    teacher = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'type': 'teacher'},
        verbose_name='講師'
    )
    
    # 通知設定
    email_notifications = models.BooleanField(
        default=True,
        verbose_name='メール通知'
    )
    
    daily_report = models.BooleanField(
        default=False,
        verbose_name='日次レポート'
    )
    
    weekly_report = models.BooleanField(
        default=True,
        verbose_name='週次レポート'
    )
    
    # 表示設定
    records_per_page = models.IntegerField(
        default=20,
        verbose_name='1ページあたりの表示件数'
    )
    
    default_period_days = models.IntegerField(
        default=7,
        verbose_name='デフォルト表示期間（日）'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')
    
    class Meta:
        verbose_name = '講師ダッシュボード設定'
        verbose_name_plural = '講師ダッシュボード設定'
    
    def __str__(self):
        return f'{self.teacher.name or self.teacher.username}の設定'

class DashboardStatistics:
    """
    ダッシュボード統計データを計算するヘルパークラス
    """
    
    @staticmethod
    def get_teacher_kiosks(teacher):
        """講師の担当キオスク一覧を取得"""
        return Kiosk.objects.filter(teacher=teacher, is_active=True)
    
    @staticmethod
    def get_today_attendance_count(teacher):
        """今日の出席者数を取得"""
        today = timezone.now().date()
        teacher_kiosks = DashboardStatistics.get_teacher_kiosks(teacher)
        
        return AttendanceRecord.objects.filter(
            kiosk__in=teacher_kiosks,
            attended_at__date=today
        ).count()
    
    @staticmethod
    def get_recent_attendance_records(teacher, limit=10):
        """最近の出席記録を取得"""
        teacher_kiosks = DashboardStatistics.get_teacher_kiosks(teacher)
        
        return AttendanceRecord.objects.filter(
            kiosk__in=teacher_kiosks
        ).select_related('user', 'kiosk').order_by('-attended_at')[:limit]
    
    @staticmethod
    def get_attendance_statistics(teacher, start_date=None, end_date=None):
        """期間別出席統計を取得"""
        if not start_date:
            start_date = timezone.now().date() - timedelta(days=7)
        if not end_date:
            end_date = timezone.now().date()
        
        teacher_kiosks = DashboardStatistics.get_teacher_kiosks(teacher)
        
        records = AttendanceRecord.objects.filter(
            kiosk__in=teacher_kiosks,
            attended_at__date__range=[start_date, end_date]
        )
        
        # 日別統計
        daily_stats = {}
        current_date = start_date
        while current_date <= end_date:
            daily_count = records.filter(attended_at__date=current_date).count()
            daily_stats[current_date.strftime('%Y-%m-%d')] = daily_count
            current_date += timedelta(days=1)
        
        return {
            'total_records': records.count(),
            'daily_stats': daily_stats,
            'period': {
                'start': start_date,
                'end': end_date
            }
        }
