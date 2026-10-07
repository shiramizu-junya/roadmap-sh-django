# Create your models here.
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    # 今は AbstractUser の項目をそのまま使う。項目を足すときはここに書く
    pass
