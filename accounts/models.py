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
    type = models.CharField(max_length=10, choices=(
        ('personal', '個人'), ('store', '店舗')), default='personal')

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