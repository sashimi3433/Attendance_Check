# attendance_token/models.py
# 出席管理用トークンモデル
from django.db import models
from django.utils import timezone
from accounts.models import CustomUser as User, Lesson
from datetime import timedelta
import secrets


class AttendanceToken(models.Model):
    """
    出席確認用トークンモデル
    ユーザーの出席確認に使用される一時的なトークンを管理
    """
    token = models.CharField(max_length=64, unique=True, db_index=True, verbose_name="出席確認トークン")
    is_used = models.BooleanField(default=False, verbose_name="使用済みフラグ")
    expires = models.DateTimeField(verbose_name="有効期限")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_tokens', verbose_name="ユーザー")
    issued_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name="発行元IPアドレス")
    created = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    def __str__(self):
        return f"出席トークン for {self.user.username} (Key: {self.token[:10]}...)"

    def mark_as_used(self):
        """トークンを使用済みとしてマークする"""
        self.is_used = True
        self.save()
        return self.is_used

    def is_expired(self):
        """トークンの有効期限が切れているかチェック"""
        return timezone.now() > self.expires

    def generate_new_token_key(self):
        """新しいトークンキーを生成し、有効期限を更新"""
        self.token = secrets.token_urlsafe(32)
        self.expires = timezone.now() + timedelta(seconds=5)
        self.save()

    @classmethod
    def cleanup_expired_tokens(cls, minutes=10):
        """
        未使用で期限切れのトークンを削除する
        
        Args:
            minutes (int): 何分前のトークンを削除するか
            
        Returns:
            tuple: (削除されたトークン数, 削除の詳細)
        """
        from datetime import timedelta
        
        cutoff_time = timezone.now() - timedelta(minutes=minutes)
        
        # 削除対象のトークンを取得
        tokens_to_delete = cls.objects.filter(
            is_used=False,
            expires__lt=cutoff_time
        )
        
        return tokens_to_delete.delete()
    
    @classmethod
    def get_cleanup_statistics(cls):
        """
        トークンのクリーンアップ統計情報を取得
        
        Returns:
            dict: 統計情報
        """
        total = cls.objects.count()
        used = cls.objects.filter(is_used=True).count()
        unused = cls.objects.filter(is_used=False).count()
        expired_unused = cls.objects.filter(
            is_used=False,
            expires__lt=timezone.now()
        ).count()
        
        return {
            'total': total,
            'used': used,
            'unused': unused,
            'expired_unused': expired_unused
        }

    class Meta:
        verbose_name = "出席確認トークン"
        verbose_name_plural = "出席確認トークン"
        ordering = ['-created']


class AttendanceRecord(models.Model):
    """
    出席記録モデル
    実際の出席確認の記録を保存
    """
    STATUS_CHOICES = [
        ('present', '出席'),
        ('late', '遅刻'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_records', verbose_name="ユーザー")
    token = models.ForeignKey(AttendanceToken, on_delete=models.CASCADE, related_name='attendance_records', verbose_name="使用トークン")
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True, related_name='attendance_records', verbose_name="レッスン")
    attended_at = models.DateTimeField(auto_now_add=True, verbose_name="出席確認日時")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="終了時間")
    location = models.CharField(max_length=100, blank=True, null=True, verbose_name="出席場所")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present', verbose_name="出席状態")
    notes = models.TextField(blank=True, null=True, verbose_name="備考")

    def __str__(self):
        return f"{self.user.username} - {self.attended_at.strftime('%Y/%m/%d %H:%M')}"

    class Meta:
        verbose_name = "出席記録"
        verbose_name_plural = "出席記録"
        ordering = ['-attended_at']
        unique_together = ['user', 'token']  # 同じユーザーが同じトークンで複数回出席確認することを防ぐ