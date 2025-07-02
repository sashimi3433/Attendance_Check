from django.contrib.auth.forms import UserChangeForm
from .models import CustomUser, grade

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'name', 'grade', 'age')
