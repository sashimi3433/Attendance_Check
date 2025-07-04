# -*- coding: utf-8 -*-
from django.urls import path, include
from django.contrib.auth import views as auth_views
from .views import profile_edit, signup, passwordless_login, admin_menu, admin_user_detail, admin_edit_user

app_name = 'accounts'

urlpatterns = [
    # カスタムログインとログアウト
    path('login/', passwordless_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # 新規登録
    path('signup/', signup, name='signup'),
    
    # プロフィール編集
    path('profile/', profile_edit, name='profile_edit'),

    # Admin-specific URLs
    path('admin/', admin_menu, name='admin_menu'),
    path('admin/user/<int:user_id>/', admin_user_detail, name='admin_user_detail'),
    path('admin/edit_user/<int:user_id>/', admin_edit_user, name='admin_edit_user'),
]