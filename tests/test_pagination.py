from ninja.testing import TestClient

from accounts.models import User
from blog.models import Post
from config.api import api

client = TestClient(api)


def test_limit_and_offset(user: User) -> None:
    for i in range(5):
        Post.objects.create(title=f"記事{i}", body="b", author=user)  # 記事0 が一番古い

    first = client.get("/posts?limit=2").json()
    assert first["count"] == 5  # count はページではなく、全部の件数
    assert [p["title"] for p in first["items"]] == ["記事4", "記事3"]  # 新しい順

    second = client.get("/posts?limit=2&offset=2").json()
    assert [p["title"] for p in second["items"]] == ["記事2", "記事1"]  # 続きから


def test_limit_zero_is_422(user: User) -> None:
    assert client.get("/posts?limit=0").status_code == 422
