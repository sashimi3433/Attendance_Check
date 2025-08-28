from django.db import models
from django.contrib.auth.models import AbstractUser
import random
import string

# 学科の選択肢
department_choices = (
    ('IT_highclass_sougou', 'ITハイクラス総合'),
    ('IT_sougou', 'IT総合'),
    ('AI_IOT_senkou', 'AI/IOT専攻'),
    ('whitehacker_senkou', 'ホワイトハッカー専攻'),
    ('teacher', '講師'),
    ('other', 'その他'),
)

class InvitationCode(models.Model):
    """
    招待コード管理モデル
    """
    code = models.CharField(max_length=5, unique=True, verbose_name='招待コード')
    name = models.CharField(max_length=50, verbose_name='名前')
    type = models.CharField(max_length=10, choices=(
        ('student', '生徒用'), ('teacher', '講師用')), default='student', verbose_name='種別')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    is_active = models.BooleanField(default=True, verbose_name='有効フラグ')
    used_count = models.IntegerField(default=0, verbose_name='使用回数')
    
    class Meta:
        verbose_name = '招待コード'
        verbose_name_plural = '招待コード'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @classmethod
    def generate_unique_code(cls):
        """
        重複しない5桁の数字コードを生成
        """
        while True:
            code = ''.join([str(random.randint(0, 9)) for _ in range(5)])
            if not cls.objects.filter(code=code).exists():
                return code
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_unique_code()
        super().save(*args, **kwargs)

class CustomUser(AbstractUser):
    name = models.CharField(max_length=20, blank=True, null=True, verbose_name='名前')
    birth_date = models.DateField(null=True, blank=True, verbose_name='生年月日')
    admission_year = models.IntegerField(null=True, blank=True, verbose_name='入学年度')
    department = models.CharField(
        max_length=30,
        choices=department_choices,
        default='other',
        verbose_name='学科'
    )
    type = models.CharField(
        max_length=10,
        choices=[('student', '生徒'), ('teacher', '講師'), ('kiosk', 'キオスク')],
        default='student',
        verbose_name='アカウント種別'
    )
    invitation_code = models.ForeignKey(
        InvitationCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='使用した招待コード'
    )



class Teacher(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, limit_choices_to={'invitation_code__type': 'teacher'}, related_name='teacher_profile')
    subject = models.CharField(max_length=20, default='デフォルト科目')

    def __str__(self):
        return f"{self.user.username} - {self.subject}"

class Kiosk(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, limit_choices_to={'type': 'kiosk'}, related_name='kiosk_profile')
    location = models.CharField(max_length=100, verbose_name='場所')
    current_lesson = models.ForeignKey('Lesson', on_delete=models.SET_NULL, null=True, blank=True, related_name='active_kiosks', verbose_name='現在のレッスン')
    is_active = models.BooleanField(default=True, verbose_name='有効')

    def __str__(self):
        return f"{self.user.username} - {self.location}"

class Lesson(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    subject = models.CharField(max_length=20)
    lesson_times = models.IntegerField(default=1)
    location = models.CharField(max_length=100, blank=True, null=True)
    lesson_date = models.DateTimeField(blank=True, null=True, verbose_name='授業日時')
    reception = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False, verbose_name='アクティブ')

    def __str__(self):
        return f"{self.subject} - {self.teacher.user.username} (第{self.lesson_times}回)"
