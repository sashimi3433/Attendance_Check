from django.contrib import admin
from django.urls import path, include
# auditlog管理画面設定をインポート
import auditlog_admin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('accounts/', include('accounts.urls')),
    path('attendance_token/', include('attendance_token.urls', namespace='attendance_token')),
    path('checkin/', include('checkin.urls', namespace='checkin')),
    path('teacher/', include('teacher_dashboard.urls', namespace='teacher_dashboard')),
]
