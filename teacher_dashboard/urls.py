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
    # path('lesson/', views.lesson, name='lesson'),
    # path('lesson/<int:pk>/', views.lesson_detail, name='lesson_detail'),
    # path('lesson/<int:pk>/attendance/', views.attendance, name='attendance'),
    # path('lesson/<int:pk>/attendance/<int:pk>/', views.attendance_detail, name='attendance_detail'),
]