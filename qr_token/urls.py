# qr_token/urls.py
from django.urls import path
from .views import token_generator # token_generatorビューをインポート

urlpatterns = [
    # このパスは、myapp/urls.pyでのインクルード設定によりプレフィックスが付きます
    path('generate-token/', token_generator, name='generate_token_api'),
]