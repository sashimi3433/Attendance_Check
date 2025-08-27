# attendance_token/urls.py
from django.urls import path
from .views import (
    token_generator, 
    get_attendance_history,
    attendance_detail
) # ビューをインポート

app_name = 'attendance_token'

urlpatterns = [
    path('generate-token/', token_generator, name='generate_token_api'),
    path('attendance-history/', get_attendance_history, name='attendance_history_api'),
    path('detail/<int:record_id>/', attendance_detail, name='attendance_detail'),
]