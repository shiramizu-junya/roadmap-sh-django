from django.db import models


class Post(models.Model):
    title = models.CharField(max_length=200)  # 短い文字列（上限200文字）
    body = models.TextField()  # 長い文章（上限なし）
    created_at = models.DateTimeField(auto_now_add=True)  # 作成時に自動で入る
    updated_at = models.DateTimeField(auto_now=True)  # 保存のたびに自動で更新

    def __str__(self) -> str:
        return self.title
