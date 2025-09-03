from django.urls import path
from . import views

app_name = 'teacher_dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('generate_lesson/', views.generate_lesson, name='generate_lesson'),
    path('start_checkin/', views.start_checkin, name='start_checkin'),
    path('list_lessons/', views.list_lessons, name='list_lessons'),
    path('edit_lesson/<int:lesson_id>/', views.edit_lesson, name='edit_lesson'),
    path('end_lesson/<int:lesson_id>/', views.end_lesson, name='end_lesson'),
    # 出席者一覧機能のURLパターン
    path('attendance_list/', views.attendance_list, name='attendance_list'),
    path('attendance_list/<int:lesson_id>/', views.attendance_list, name='attendance_list_lesson'),
    path('attendance_detail/<int:record_id>/', views.attendance_detail, name='attendance_detail'),
    path('attendance_export/<int:lesson_id>/', views.attendance_export, name='attendance_export'),
]