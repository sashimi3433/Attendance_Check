from django.urls import path
from . import views

app_name = 'pos'

urlpatterns = [
    path('', views.view_dashboard, name='view_dashboard'),
]