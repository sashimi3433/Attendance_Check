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
    balance = models.IntegerField(default=200)
    name = models.CharField(max_length=20, blank=True, null=True, verbose_name='名前')
    birth_date = models.DateField(null=True, blank=True, verbose_name='生年月日')
    admission_year = models.IntegerField(null=True, blank=True, verbose_name='入学年度')
    department = models.CharField(
        max_length=30, 
        choices=department_choices, 
        default='other', 
        verbose_name='学科'
    )
    type = models.CharField(max_length=10, choices=(
        ('student', '生徒'), ('teacher', '講師'), ('kiosk', 'キオスク')), default='student', verbose_name='アカウント種別')
    invitation_code = models.ForeignKey(
        InvitationCode, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name='使用した招待コード'
    )

class Kiosk(models.Model):
    """
    キオスク端末管理モデル
    """
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        limit_choices_to={'type': 'kiosk'},
        verbose_name='キオスクユーザー'
    )
    name = models.CharField(max_length=50, verbose_name='キオスク名')
    location = models.CharField(max_length=100, verbose_name='設置場所')
    teacher = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'type': 'teacher'},
        related_name='kiosk_teacher',
        verbose_name='担当講師'
    )
    is_active = models.BooleanField(default=True, verbose_name='有効フラグ')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')
    
    class Meta:
        verbose_name = 'キオスク'
        verbose_name_plural = 'キオスク'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.location})"

class Transaction(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    amount = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)
    account_type = models.CharField(max_length=10, choices=(('income', '入金'), ('expense', '出金')))
    description = models.CharField(max_length=100, blank=True, null=True)

class Store(models.Model):
    name = models.CharField(max_length=20)
    balance = models.IntegerField(default=0)
    items = models.ManyToManyField('Item')

class Item(models.Model):
    name = models.CharField(max_length=20)
    price = models.IntegerField()
    dealer = models.ManyToManyField(Store)
    stock = models.IntegerField()
    sold_out = models.BooleanField(default=False)
    
class Teaching(models.Model):
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'type': 'teacher'})
    subject = models.CharField(max_length=20)
    location = models.CharField(max_length=100)
    times = models.IntegerField(default=0)
