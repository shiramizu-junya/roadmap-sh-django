# Create your views here.
from django.http import HttpRequest, JsonResponse

from .models import Post


def post_list(request: HttpRequest) -> JsonResponse:
    # 台帳（blog_post）から全件を取り出す。この時点ではまだ SQL は飛ばない
    posts = Post.objects.all()

    # 1件ずつ辞書に組み直す。ここで初めて SQL が1本飛ぶ
    data = [
        {
            "id": post.id,
            "title": post.title,
            "body": post.body,
            "created_at": post.created_at,
        }
        for post in posts
    ]

    # 辞書ではなくリストを返すので safe=False が要る
    return JsonResponse(data, safe=False)
