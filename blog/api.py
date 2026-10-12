from datetime import datetime

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Field, Router, Schema, Status

from .models import Category, Post, Tag

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


@router.get("", response=list[PostOut])
def list_posts(request: HttpRequest):
    return Post.objects.all()


@router.post("", response={201: PostOut})
def create_post(request: HttpRequest, payload: PostIn):
    category = None
    if payload.category_id is not None:
        category = get_object_or_404(Category, id=payload.category_id)
    # 無いタグが1つでもあれば 404（記事を作る前に確かめる）
    tags = [get_object_or_404(Tag, id=tag_id) for tag_id in payload.tag_ids]
    post = Post.objects.create(title=payload.title, body=payload.body, category=category)
    post.tags.set(tags)  # つなぎの台帳（blog_post_tags）に行を入れる
    return Status(201, post)


@router.get("/{post_id}", response=PostOut)
def get_post(request: HttpRequest, post_id: int):
    return get_object_or_404(Post, id=post_id)


@router.patch("/{post_id}", response=PostOut)
def update_post(request: HttpRequest, post_id: int, payload: PostPatch):
    post = get_object_or_404(Post, id=post_id)
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    for name, value in changes.items():
        setattr(post, name, value)
    post.save()
    return post


@router.delete("/{post_id}", response={204: None})
def delete_post(request: HttpRequest, post_id: int):
    post = get_object_or_404(Post, id=post_id)
    post.delete()
    return Status(204, None)
