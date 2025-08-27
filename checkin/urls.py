# checkin/urls.py
from django.urls import path
from .views import (
    success_page,
    error_page,
    qr_scanner,
    confirm_attendance,
)

app_name = 'checkin'

urlpatterns = [
    path('success/', success_page, name='success'),
    path('error/', error_page, name='error'),
    path('qr_scanner/', qr_scanner, name='qr_scanner'),
    path('confirm-attendance/', confirm_attendance, name='confirm_attendance'),
]