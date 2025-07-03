from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class PasswordlessAuthBackend(BaseBackend):
    """
    パスワードなしでの認証を可能にするカスタム認証バックエンド
    """
    
    def authenticate(self, request, username=None, **kwargs):
        """
        ユーザー名のみで認証を行う
        """
        if username is None:
            return None
            
        try:
            user = User.objects.get(username=username)
            return user
        except User.DoesNotExist:
            return None
    
    def get_user(self, user_id):
        """
        ユーザーIDからユーザーオブジェクトを取得
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None