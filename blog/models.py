from django.conf import settings
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=30, unique=True)

    def __str__(self) -> str:
        return self.name


class Post(models.Model):
    title = models.CharField(max_length=200)  # 短い文字列（上限200文字）
    body = models.TextField()  # 長い文章（上限なし）
    created_at = models.DateTimeField(auto_now_add=True)  # 作成時に自動で入る
    updated_at = models.DateTimeField(auto_now=True)  # 保存のたびに自動で更新
    # 多対一: 1つの記事は1つのカテゴリに属する（カテゴリには多くの記事）
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,  # 記事が残っているカテゴリは消せない
        null=True,  # 既存の記事にはカテゴリが無いので、空を許す
        blank=True,  # 管理画面の入力欄も空でよい
    )
    # 多対多: 1つの記事に複数のタグ、1つのタグに複数の記事
    tags = models.ManyToManyField(Tag, blank=True)
    # 多対一: 記事を書いた人。ユーザーを消すと、その人の記事も消える
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # accounts.User を指す（1-2 の設定）
        on_delete=models.CASCADE,
        null=True,  # 既存の記事には書いた人がいないので、空を許す
        blank=True,
    )

    def __str__(self) -> str:
        return self.title


class Comment(models.Model):
    # related_name: 記事の側から post.comments で引けるようにする
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # 自己参照: 返信なら返信先のコメント。最初のコメントなら空
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,  # 親コメントを消すと、返信も消える
        null=True,
        blank=True,
        related_name="replies",  # 親コメントから comment.replies で返信を引く
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.body[:20]
