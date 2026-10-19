from ninja.testing import TestClient

from accounts.models import User
from blog.models import Post
from config.api import api

client = TestClient(api)


def test_delete_keeps_row(user: User, auth_headers: dict[str, str]) -> None:
    post = Post.objects.create(title="t", body="b", author=user)
    assert client.delete(f"/posts/{post.id}", headers=auth_headers).status_code == 204

    assert Post.objects.count() == 0  # ふだんの窓口からは見えない
    assert Post.all_objects.count() == 1  # 行は残っている
    assert Post.all_objects.get(id=post.id).deleted_at is not None  # 消した日時が入った


def test_deleted_post_is_hidden(user: User, auth_headers: dict[str, str]) -> None:
    alive = Post.objects.create(title="残す", body="b", author=user)
    gone = Post.objects.create(title="消す", body="b", author=user)
    client.delete(f"/posts/{gone.id}", headers=auth_headers)

    assert [p["title"] for p in client.get("/posts").json()["items"]] == [alive.title]
    assert client.get(f"/posts/{gone.id}").status_code == 404
