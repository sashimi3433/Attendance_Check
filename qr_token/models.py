from django.db import models
from accounts.models import CustomUser as User
from datetime import datetime, timedelta
import secrets



class QR_Token(models.Model):
    token = models.CharField(max_length=64, unique=True, db_index=True)
    is_used = models.BooleanField(default=False)
    expires = models.DateTimeField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='qr_tokens')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    usage = models.Choices

    def __str__(self):
        return f"QR_Token for {self.user.username} (Key: {self.token[:10]}...)"

    def mark_as_used(self):
        self.is_used = True
        self.save()
        return self.is_used

    def is_expired(self):
        return datetime.now() > self.expires

    def generate_new_token_key(self):
        self.token = secrets.token_urlsafe(32)
        self.expires = datetime.now() + timedelta(minutes=5)
        self.save()