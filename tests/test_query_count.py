import pytest
from ninja.testing import TestClient

from blog.models import Category, Post, Tag
from config.api import api

client = TestClient(api)


@pytest.mark.django_db
@pytest.mark.parametrize("n_posts", [3, 10])  # 記事3件と10件で、同じテストを2回流す
def test_list_posts_query_count_does_not_grow(n_posts: int, django_assert_num_queries) -> None:
    category = Category.objects.create(name="日記")
    tags = [Tag.objects.create(name="python"), Tag.objects.create(name="django")]
    for i in range(n_posts):
        post = Post.objects.create(title=f"記事{i}", body="b", category=category)
        post.tags.set(tags)

    # この中で出た SQL がちょうど2本でなければ失敗する
    with django_assert_num_queries(2):
        res = client.get("/posts")

    assert res.status_code == 200
    assert len(res.json()) == n_posts
