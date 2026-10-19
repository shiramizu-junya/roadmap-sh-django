import pytest
from ninja.testing import TestClient

from blog.models import Category, Post
from config.api import api

client = TestClient(api)


@pytest.fixture
def posts(db) -> None:
    # 検索の材料: 記事3件。カテゴリは「技術」1件と「日記」2件
    tech = Category.objects.create(name="技術")
    diary = Category.objects.create(name="日記")
    Post.objects.create(title="Ninja で作った", body="API を書いた", category=tech)
    Post.objects.create(title="今日の日記", body="django を少し触った", category=diary)
    Post.objects.create(title="三つ目の投稿", body="ninja の話はしない", category=diary)


def titles(url: str) -> set[str]:
    # 並び順はまだ決めていない（2-12 で扱う）ので、集合にして比べる
    return {p["title"] for p in client.get(url).json()}


def test_q_searches_title_and_body(posts: None) -> None:
    # 大文字・小文字は区別しない。タイトルと本文のどちらに含まれていても当たる
    assert titles("/posts?q=NINJA") == {"Ninja で作った", "三つ目の投稿"}


def test_empty_q_returns_all(posts: None) -> None:
    assert len(titles("/posts?q=")) == 3


def test_q_and_category_are_and(posts: None) -> None:
    diary = Category.objects.get(name="日記")
    assert titles(f"/posts?q=ninja&category_id={diary.id}") == {"三つ目の投稿"}
