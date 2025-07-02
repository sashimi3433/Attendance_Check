from django.urls import path, include
from .views import profile_edit

app_name = 'accounts'

urlpatterns = [
    path('', include('django.contrib.auth.urls')),
    path('profile/', profile_edit, name='profile_edit'),
]
