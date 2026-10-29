from decimal import Decimal

import pytest
from ninja.testing import TestClient

from accounts.models import User
from blog.models import Category
from config.api import api
from shop.models import Inventory, Product, Review

client = TestClient(api)


@pytest.fixture
def book(db) -> Product:
    category = Category.objects.create(name="本")
    product = Product.objects.create(name="Django 入門", price=Decimal("2980"), category=category)
    Inventory.objects.create(product=product, quantity=5)  # 在庫の行が無いと、商品の応答が 500
    return product


def test_rating_is_counted(user: User, book: Product) -> None:
    bob = User.objects.create_user(username="bob", password="pass1234")
    Review.objects.create(product=book, user=user, rating=4)
    Review.objects.create(product=book, user=bob, rating=5)

    body = client.get(f"/products/{book.id}").json()

    assert body["review_count"] == 2
    assert body["rating_avg"] == 4.5  # (4 + 5) / 2


def test_review_twice_is_409(book: Product, auth_headers: dict[str, str]) -> None:
    url = f"/products/{book.id}/reviews"
    assert client.post(url, json={"rating": 5}, headers=auth_headers).status_code == 201

    res = client.post(url, json={"rating": 1}, headers=auth_headers)

    assert res.status_code == 409
    assert Review.objects.count() == 1


def test_rating_must_be_1_to_5(book: Product, auth_headers: dict[str, str]) -> None:
    res = client.post(f"/products/{book.id}/reviews", json={"rating": 6}, headers=auth_headers)

    assert res.status_code == 422
