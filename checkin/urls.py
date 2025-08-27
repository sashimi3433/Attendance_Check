# checkin/urls.py
from django.urls import path
from .views import (
    confirm_attendance,
    qr_scanner,
    success_page,
    error_page,
)

app_name = 'checkin'

urlpatterns = [
    path('', qr_scanner, name='qr_scanner'),
    path('confirm-attendance/', confirm_attendance, name='confirm_attendance_api'),
    path('success/', success_page, name='success'),
    path('error/', error_page, name='error'),
]