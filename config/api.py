from django.http import HttpRequest
from ninja import Field, NinjaAPI, Schema

from blog.models import Post
from blog.views import post_to_dict  # 返す形は 1-6 の手書き版を使い回す

api = NinjaAPI()


class PostIn(Schema):
    # 申請書の書式: 何を・どの型で・どんな条件で受け取るか
    title: str = Field(max_length=200)
    body: str


@api.get("/posts")
def list_posts(request: HttpRequest) -> list[dict[str, object]]:
    return [post_to_dict(post) for post in Post.objects.all()]


@api.post("/posts")
def create_post(request: HttpRequest, payload: PostIn) -> dict[str, object]:
    # ここに来た時点で、payload は検査済み（title も body も str）
    post = Post.objects.create(title=payload.title, body=payload.body)
    return post_to_dict(post)
