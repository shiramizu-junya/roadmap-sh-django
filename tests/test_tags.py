import pytest
from ninja.testing import TestClient

from blog.models import Post, Tag
from config.api import api

client = TestClient(api)


@pytest.mark.django_db
def test_create_post_with_tags(auth_headers: dict[str, str]) -> None:
    python = Tag.objects.create(name="python")
    django = Tag.objects.create(name="django")

    res = client.post(
        "/posts",
        json={"title": "t", "body": "b", "tag_ids": [python.id, django.id]},
        headers=auth_headers,
    )
    assert res.status_code == 201
    # 並び順は保証されないので、並べ替えてから比べる
    assert sorted(tag["name"] for tag in res.json()["tags"]) == ["django", "python"]


@pytest.mark.django_db
def test_unknown_tag_is_404_and_nothing_saved(auth_headers: dict[str, str]) -> None:
    res = client.post(
        "/posts", json={"title": "t", "body": "b", "tag_ids": [999]}, headers=auth_headers
    )
    assert res.status_code == 404
    assert Post.objects.count() == 0
