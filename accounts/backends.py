from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class PasswordlessAuthBackend(BaseBackend):
    """
    パスワードなしでの認証を可能にするカスタム認証バックエンド
    """
    
    def authenticate(self, request, username=None, name=None, grade=None, age=None, **kwargs):
        """
        ユーザー名、名前、学年、年齢で認証を行う
        """
        if username is None or name is None or grade is None or age is None:
            return None
            
        try:
            user = User.objects.get(
                username=username,
                name=name,
                grade=grade,
                age=age
            )
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