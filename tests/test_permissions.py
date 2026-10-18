import pytest
from ninja.testing import TestClient

from accounts.models import User
from blog.models import Post
from config.api import api

client = TestClient(api)


@pytest.mark.django_db
def test_create_without_token_is_401() -> None:
    res = client.post("/posts", json={"title": "t", "body": "b"})
    # TODO: 401 で、記事が保存されていないこと
    assert res.status_code == 401
    assert Post.objects.count() == 0


def test_create_sets_author(user: User, auth_headers: dict[str, str]) -> None:
    res = client.post("/posts", json={"title": "t", "body": "b"}, headers=auth_headers)
    # TODO: 応答の author_id が、ログインしている人の id であること
    assert res.json()["author_id"] == user.id


def test_cannot_change_others_post(auth_headers: dict[str, str]) -> None:
    bob = User.objects.create_user(username="bob", password="pass1234")
    post = Post.objects.create(title="bob の記事", body="b", author=bob)
    # TODO: alice（auth_headers）が bob の記事を変更・削除すると 403。記事はそのまま
    res = client.patch(f"/posts/{post.id}", json={"title": "乗っ取り"}, headers=auth_headers)
    assert res.status_code == 403
    assert client.delete(f"/posts/{post.id}", headers=auth_headers).status_code == 403
    assert Post.objects.get(id=post.id).title == "bob の記事"
