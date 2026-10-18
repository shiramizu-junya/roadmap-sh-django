import pytest
from ninja.testing import TestClient

from accounts.models import User
from blog.models import Post
from config.api import api

# Ninja の API を、サーバを起動せずに直接呼ぶためのクライアント
client = TestClient(api)


@pytest.mark.django_db  # このテストは DB を使う（テスト用 DB が作られる）
def test_create_and_get_post(auth_headers: dict[str, str]) -> None:
    res = client.post("/posts", json={"title": "テスト", "body": "本文"}, headers=auth_headers)
    assert res.status_code == 201
    post_id = res.json()["id"]

    res = client.get(f"/posts/{post_id}")
    assert res.status_code == 200
    assert res.json()["title"] == "テスト"


@pytest.mark.django_db
def test_create_rejects_long_title(auth_headers: dict[str, str]) -> None:
    res = client.post("/posts", json={"title": "a" * 201, "body": "本文"}, headers=auth_headers)
    assert res.status_code == 422
    assert Post.objects.count() == 0  # 保存されていない


@pytest.mark.django_db
def test_update_changes_only_sent_fields(user: User, auth_headers: dict[str, str]) -> None:
    post = Post.objects.create(title="元の題名", body="元の本文", author=user)

    res = client.patch(f"/posts/{post.id}", json={"title": "新しい題名"}, headers=auth_headers)
    assert res.status_code == 200

    saved = Post.objects.get(id=post.id)  # DB から読み直す
    assert saved.title == "新しい題名"
    assert saved.body == "元の本文"  # 送らなかった項目は変わらない


@pytest.mark.django_db
def test_delete_then_404(user: User, auth_headers: dict[str, str]) -> None:
    post = Post.objects.create(title="消す", body="本文", author=user)

    assert client.delete(f"/posts/{post.id}", headers=auth_headers).status_code == 204
    assert client.get(f"/posts/{post.id}").status_code == 404
