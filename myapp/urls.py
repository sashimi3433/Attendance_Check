from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    # path('show_qr/', include('show_qr.urls')),
    # path('accounts/', include('accounts.urls')),
    path('accounts/', include('accounts.urls')),
    path('api/', include('qr_token.urls')),
]
