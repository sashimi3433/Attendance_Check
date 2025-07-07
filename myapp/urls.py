from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('accounts/', include('accounts.urls')),
    path('api/', include('qr_token.urls', namespace='qr_token')),
    path('adminmenu/', include('adminmenu.urls', namespace='adminmenu')),
    path('pos/', include('pos.urls', namespace='pos')),
]
