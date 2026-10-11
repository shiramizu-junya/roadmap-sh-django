from datetime import datetime

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Field, NinjaAPI, Schema, Status

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


class PostPatch(Schema):
    # 更新の書式。どの項目も省略してよい（省略した項目は変えない）
    title: str | None = Field(default=None, max_length=200)
    body: str | None = None


@api.get("/posts", response=list[PostOut])
def list_posts(request: HttpRequest):  # 戻り値の形は response= で宣言する
    return Post.objects.all()


@api.post("/posts", response={201: PostOut})
def create_post(request: HttpRequest, payload: PostIn):
    post = Post.objects.create(title=payload.title, body=payload.body)
    return Status(201, post)  # (ステータス, 中身) の組で返す


@api.get("/posts/{post_id}", response=PostOut)
def get_post(request: HttpRequest, post_id: int):
    # {post_id} の部分が、同じ名前の引数に int で渡される
    return get_object_or_404(Post, id=post_id)  # 無ければ 404


@api.patch("/posts/{post_id}", response=PostOut)
def update_post(request: HttpRequest, post_id: int, payload: PostPatch):
    post = get_object_or_404(Post, id=post_id)
    # 送られてきた項目だけを取り出す（省略した項目・null の項目は入らない）
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    for name, value in changes.items():
        setattr(post, name, value)  # post.title = value と同じ
    post.save()
    return post


@api.delete("/posts/{post_id}", response={204: None})
def delete_post(request: HttpRequest, post_id: int):
    post = get_object_or_404(Post, id=post_id)
    post.delete()
    return Status(204, None)  # 204 は「成功。返す中身は無い」
