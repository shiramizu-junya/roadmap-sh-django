import json

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Post


def post_to_dict(post: Post) -> dict[str, object]:
    # 1件の Post を、返す形（辞書）に組み直す
    return {
        "id": post.id,
        "title": post.title,
        "body": post.body,
        "created_at": post.created_at,
    }


@csrf_exempt  # このビューだけ CSRF の検査を外す（理由は 6-2）
def post_list(request: HttpRequest) -> JsonResponse:
    if request.method == "GET":
        data = [post_to_dict(post) for post in Post.objects.all()]
        return JsonResponse(data, safe=False)

    if request.method == "POST":
        return create_post(request)

    return JsonResponse({"detail": "許可されていないメソッドです"}, status=405)


def create_post(request: HttpRequest) -> JsonResponse:
    # ① 本文を JSON として読む
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"detail": "JSON として読めません"}, status=400)

    if not isinstance(payload, dict):
        return JsonResponse({"detail": "JSON はオブジェクトで送ってください"}, status=400)

    # ② 必須チェックと型チェック。エラーは項目ごとに集める
    errors: dict[str, str] = {}
    title = payload.get("title")
    body = payload.get("body")

    if title is None:
        errors["title"] = "必須です"
    elif not isinstance(title, str):
        errors["title"] = "文字列で送ってください"
    elif len(title) > 200:
        errors["title"] = "200文字以内にしてください"

    if body is None:
        errors["body"] = "必須です"
    elif not isinstance(body, str):
        errors["body"] = "文字列で送ってください"

    # isinstance も条件に入れると、この先で両方が str だと mypy にも伝わる
    if errors or not isinstance(title, str) or not isinstance(body, str):
        return JsonResponse({"errors": errors}, status=400)

    # ③ 保存して、作ったものを 201 で返す
    post = Post.objects.create(title=title, body=body)
    return JsonResponse(post_to_dict(post), status=201)
