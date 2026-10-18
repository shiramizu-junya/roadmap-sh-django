from datetime import datetime

from django.core.files.images import get_image_dimensions
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Field, Router, Schema, Status, UploadedFile
from ninja.errors import HttpError
from ninja_jwt.authentication import JWTAuth

from .models import Category, Comment, Post, PostImage, Tag

# 記事の API 一式。URL の頭（/posts）は config/api.py で決める
router = Router()


class PostIn(Schema):
    title: str = Field(max_length=200)
    body: str
    category_id: int | None = None  # 省略したらカテゴリなし
    tag_ids: list[int] = []  # 付けるタグの id。省略したらタグなし


class TagOut(Schema):
    id: int
    name: str


class CategoryOut(Schema):
    id: int
    name: str


class PostPatch(Schema):
    title: str | None = Field(default=None, max_length=200)
    body: str | None = None


class PostOut(Schema):
    id: int
    title: str
    body: str
    created_at: datetime
    category_id: int | None
    tags: list[TagOut]  # 入れ子: 記事の中にタグの一覧を入れて返す
    category: CategoryOut | None  # 入れ子: カテゴリの名前も返す
    author_id: int | None  # 書いた人の id（既存の記事は null）


@router.get("", response=list[PostOut])
def list_posts(request: HttpRequest):
    return (
        Post.objects.select_related("category")  # カテゴリは JOIN で同じ SQL に入れる
        .prefetch_related("tags")  # タグは別の SQL 1本でまとめて取る
        .all()
    )


@router.post("", response={201: PostOut}, auth=JWTAuth())  # 身分証が無ければ 401
def create_post(request: HttpRequest, payload: PostIn):
    category = None
    if payload.category_id is not None:
        category = get_object_or_404(Category, id=payload.category_id)
    # 無いタグが1つでもあれば 404（記事を作る前に確かめる）
    tags = [get_object_or_404(Tag, id=tag_id) for tag_id in payload.tag_ids]
    post = Post.objects.create(
        title=payload.title,
        body=payload.body,
        category=category,
        # 身分証の持ち主を、書いた人にする。author=request.user だと mypy が型違いを指摘する
        author_id=request.user.id,
    )
    post.tags.set(tags)
    return Status(201, post)


@router.get("/{post_id}", response=PostOut)
def get_post(request: HttpRequest, post_id: int):
    return get_object_or_404(Post, id=post_id)


@router.patch("/{post_id}", response=PostOut, auth=JWTAuth())
def update_post(request: HttpRequest, post_id: int, payload: PostPatch):
    post = get_object_or_404(Post, id=post_id)
    if post.author_id != request.user.id:
        raise HttpError(403, "自分の記事しか変更できません")
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    for name, value in changes.items():
        setattr(post, name, value)
    post.save()
    return post


@router.delete("/{post_id}", response={204: None}, auth=JWTAuth())
def delete_post(request: HttpRequest, post_id: int):
    post = get_object_or_404(Post, id=post_id)
    if post.author_id != request.user.id:
        raise HttpError(403, "自分の記事しか削除できません")
    post.delete()
    return Status(204, None)


class CommentIn(Schema):
    body: str = Field(min_length=1)
    parent_id: int | None = None  # 返信なら返信先のコメントの id


class ReplyOut(Schema):
    id: int
    author_id: int
    body: str
    created_at: datetime


class CommentOut(ReplyOut):
    replies: list[ReplyOut]  # 入れ子: このコメントへの返信


@router.post("/{post_id}/comments", response={201: CommentOut}, auth=JWTAuth())
def create_comment(request: HttpRequest, post_id: int, payload: CommentIn):
    post = get_object_or_404(Post, id=post_id)
    parent = None
    if payload.parent_id is not None:
        # 返信先は、同じ記事のコメントに限る（違う記事なら 404）
        parent = get_object_or_404(Comment, id=payload.parent_id, post=post)
        if parent.parent_id is not None:
            raise HttpError(400, "返信には返信できません")
    # JWTAuth を通ったので必ずログイン済み。mypy に「User だ」と伝える
    assert request.user.is_authenticated
    comment = Comment.objects.create(
        post=post, author=request.user, parent=parent, body=payload.body
    )
    return Status(201, comment)


@router.get("/{post_id}/comments", response=list[CommentOut])
def list_comments(request: HttpRequest, post_id: int):
    post = get_object_or_404(Post, id=post_id)
    # post.comments: related_name で付けた、記事からコメントへの入口
    return post.comments.filter(parent=None).prefetch_related("replies")


class PostImageOut(Schema):
    id: int
    url: str = Field(alias="image.url")  # 保存したファイルを見に行く URL


@router.post("/{post_id}/images", response={201: PostImageOut}, auth=JWTAuth())
def upload_image(request: HttpRequest, post_id: int, file: UploadedFile):
    post = get_object_or_404(Post, id=post_id)
    if post.author_id != request.user.id:
        raise HttpError(403, "自分の記事にしか画像を付けられません")
    # 大きすぎるファイルは断る（size は不明のとき None になりうる）
    if file.size is None or file.size > 2 * 1024 * 1024:
        raise HttpError(400, "画像は 2MB までです")
    # Pillow で中身を読んで、本当に画像か確かめる（画像でなければ幅と高さが None）
    width, _ = get_image_dimensions(file)
    if width is None:
        raise HttpError(400, "画像ファイルを送ってください")
    post_image = PostImage.objects.create(post=post, image=file)
    return Status(201, post_image)
