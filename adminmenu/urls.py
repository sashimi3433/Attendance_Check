# -*- coding: utf-8 -*-
from django.urls import path
from . import views

app_name = 'adminmenu'

urlpatterns = [
    path('', views.admin_menu, name='menu'),
    path('user/<int:user_id>/', views.user_detail, name='user_detail'),
    path('edit_user/<int:user_id>/', views.edit_user, name='edit_user'),
]
