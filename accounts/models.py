from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    balance = models.IntegerField(default=200)