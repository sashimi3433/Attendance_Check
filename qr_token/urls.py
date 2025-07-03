# qr_token/urls.py
from django.urls import path
from .views import token_generator # token_generatorビューをインポート

app_name = 'qr_token'

urlpatterns = [
    path('generate-token/', token_generator, name='generate_token_api'),
]