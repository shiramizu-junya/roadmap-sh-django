from decimal import Decimal

import pytest
from ninja.testing import TestClient

from blog.models import Category
from config.api import api
from shop.models import CartItem, Product

client = TestClient(api)


@pytest.fixture
def book(db) -> Product:
    category = Category.objects.create(name="本")
    return Product.objects.create(name="Django 入門", price=Decimal("2980"), category=category)


def test_same_product_is_added_up(book: Product, auth_headers: dict[str, str]) -> None:
    client.post("/cart/items", json={"product_id": book.id}, headers=auth_headers)
    res = client.post(
        "/cart/items", json={"product_id": book.id, "quantity": 2}, headers=auth_headers
    )

    assert res.status_code == 201
    assert res.json()["quantity"] == 3  # 1 + 2
    assert CartItem.objects.count() == 1  # 行は1つのまま


def test_get_cart_with_total(book: Product, auth_headers: dict[str, str]) -> None:
    client.post("/cart/items", json={"product_id": book.id, "quantity": 2}, headers=auth_headers)

    body = client.get("/cart", headers=auth_headers).json()
    assert body["items"] == [
        {"product_id": book.id, "name": "Django 入門", "price": "2980.00", "quantity": 2}
    ]
    assert body["total"] == "5960.00"


def test_cart_needs_login(book: Product) -> None:
    assert client.get("/cart").status_code == 401
