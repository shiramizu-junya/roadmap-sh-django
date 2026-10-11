from datetime import datetime

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Field, NinjaAPI, Schema

from blog.models import Post

api = NinjaAPI()


class PostIn(Schema):
    # 受け取る書式（入力）
    title: str = Field(max_length=200)
    body: str


class PostOut(Schema):
    # 返す書式（出力）。ここに無い項目は返さない
    id: int
    title: str
    body: str
    created_at: datetime


@api.get("/posts", response=list[PostOut])
def list_posts(request: HttpRequest):  # 戻り値の形は response= で宣言する
    return Post.objects.all()


@api.post("/posts", response={201: PostOut})
def create_post(request: HttpRequest, payload: PostIn):
    post = Post.objects.create(title=payload.title, body=payload.body)
    return 201, post  # (ステータス, 中身) の組で返す


@api.get("/posts/{post_id}", response=PostOut)
def get_post(request: HttpRequest, post_id: int):
    # {post_id} の部分が、同じ名前の引数に int で渡される
    return get_object_or_404(Post, id=post_id)  # 無ければ 404
