from django.urls import path
from . import views

app_name = 'teacher_dashboard'

urlpatterns = [
    # ダッシュボードホーム
    path('', views.dashboard_home, name='dashboard_home'),
    
    # キオスク管理
    path('kiosks/', views.kiosk_management, name='kiosk_management'),
    path('kiosks/<int:kiosk_id>/', views.kiosk_detail, name='kiosk_detail'),
    
    # 出席履歴
    path('attendance/', views.attendance_history, name='attendance_history'),
    path('attendance/export/', views.attendance_export, name='attendance_export'),
    
    # 統計・分析
    path('statistics/', views.statistics_analysis, name='statistics_analysis'),
    path('api/statistics/', views.statistics_api, name='statistics_api'),
    
    # ダッシュボードAPI
    path('api/dashboard-stats/', views.dashboard_stats_api, name='dashboard_stats_api'),
    
    # 設定
    path('settings/', views.settings_view, name='settings'),
]