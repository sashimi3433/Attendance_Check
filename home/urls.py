from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.index, name='index'),
    path('account/', views.account, name='account'),
    # path('qr/', views.qr, name='qr'),
    # path('qr/<int:pk>/', views.qr_detail, name='qr_detail'),
    # path('qr/<int:pk>/pay/', views.pay, name='pay'),
    # path('qr/<int:pk>/pay/confirm/', views.pay_confirm, name='pay_confirm'),
    # path('qr/<int:pk>/pay/complete/', views.pay_complete, name='pay_complete'),
]