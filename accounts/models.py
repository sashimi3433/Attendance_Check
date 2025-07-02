from django.db import models
from django.contrib.auth.models import AbstractUser

grade = (
    ('1', '1年生'),
    ('2', '2年生'),
    ('3', '3年生'),
    ('4', '4年生'),
    ('5', '5年生'),
    ('6', '6年生'),
    ('Other', 'その他'),
)

class CustomUser(AbstractUser):
    balance = models.IntegerField(default=200)
    grade = models.CharField(max_length=10, choices=grade, default='Other')
    age = models.IntegerField(default=0)
    name = models.CharField(max_length=20, blank=True, null=True)