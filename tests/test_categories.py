import pytest
from django.db.models import ProtectedError
from ninja.testing import TestClient

from blog.models import Category, Post
from config.api import api

client = TestClient(api)


@pytest.mark.django_db
def test_create_post_with_category(auth_headers: dict[str, str]) -> None:
    category = Category.objects.create(name="日記")
    res = client.post(
        "/posts", json={"title": "t", "body": "b", "category_id": category.id}, headers=auth_headers
    )
    # TODO: ステータスが 201 で、応答の category_id が category.id であること
    assert res.status_code == 201
    assert res.json()["category_id"] == category.id


@pytest.mark.django_db
def test_unknown_category_is_404(auth_headers: dict[str, str]) -> None:
    res = client.post(
        "/posts", json={"title": "t", "body": "b", "category_id": 999}, headers=auth_headers
    )
    # TODO: ステータスが 404 で、記事が1件も保存されていないこと
    assert res.status_code == 404
    assert Post.objects.count() == 0


@pytest.mark.django_db
def test_category_in_use_cannot_be_deleted() -> None:
    category = Category.objects.create(name="日記")
    Post.objects.create(title="t", body="b", category=category)

    with pytest.raises(ProtectedError):  # この中で ProtectedError が起きれば合格
        category.delete()
