# -*- coding: utf-8 -*-
from django.urls import path, include
from django.contrib.auth import views as auth_views
from .views import (
    profile_edit, signup, custom_login, custom_logout,
    export_students_csv, import_students_csv, student_management
)

app_name = 'accounts'

urlpatterns = [
    # カスタムログインとログアウト
    path('login/', custom_login, name='login'),
    path('logout/', custom_logout, name='logout'),
    
    # 新規登録
    path('signup/', signup, name='signup'),
    
    # プロフィール編集
    path('profile/', profile_edit, name='profile_edit'),
    
    # 生徒管理（CSV機能）
    path('students/', student_management, name='student_management'),
    path('students/export/', export_students_csv, name='export_students_csv'),
    path('students/import/', import_students_csv, name='import_students_csv'),

]