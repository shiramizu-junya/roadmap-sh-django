# Create your models here.
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    # 今は AbstractUser の項目をそのまま使う。項目を足すときはここに書く
    pass


class Profile(models.Model):
    # 一対一: 1人のユーザーに、プロフィールは1つだけ
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)  # 自己紹介。空でもよい

    def __str__(self) -> str:
        return f"{self.user_id} のプロフィール"
