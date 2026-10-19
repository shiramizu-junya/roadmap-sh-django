from django.conf import settings
from django.db import models
from django.utils import timezone


class AliveManager(models.Manager):
    # ふだん使う窓口。消した印（deleted_at）が付いていない行だけを返す
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class SoftDeleteModel(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True)  # 消した日時。消していなければ空

    # 先に書いた窓口が「既定の窓口」になる。get_object_or_404 や管理画面はこちらを使う
    objects = AliveManager()  # Post.objects: 消していない行だけ
    all_objects = models.Manager()  # noqa: DJ012  Post.all_objects: 消した行も含めて全部

    class Meta:
        abstract = True  # この台帳（テーブル）は作らない。継承したモデルに項目を配るだけ

    def soft_delete(self) -> None:
        # 行は消さずに、消した日時を書き込む
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=30, unique=True)

    def __str__(self) -> str:
        return self.name


class Post(SoftDeleteModel):
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


class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="images")
    # ファイルは MEDIA_ROOT/posts/ に置き、台帳にはパスの文字列だけを入れる
    image = models.ImageField(upload_to="posts/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.image.name
