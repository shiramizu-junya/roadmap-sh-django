from decimal import Decimal

import pytest
from ninja.testing import TestClient

from accounts.models import User
from blog.models import Category
from config.api import api
from shop.models import Order, OrderItem, Product

client = TestClient(api)


def make_orders(user: User, n: int) -> None:
    # 商品2つを1個ずつ買った注文を、n 件作る
    category = Category.objects.create(name=f"本{n}")
    books = [
        Product.objects.create(name=f"本{i}", price=Decimal("100"), category=category)
        for i in range(2)
    ]
    for _ in range(n):
        order = Order.objects.create(user=user, total=Decimal("200"))
        for book in books:
            OrderItem.objects.create(order=order, product=book, price=book.price, quantity=1)


def test_only_my_orders_newest_first(user: User, auth_headers: dict[str, str]) -> None:
    make_orders(user, 2)
    make_orders(User.objects.create_user(username="bob", password="pass1234"), 1)

    body = client.get("/orders", headers=auth_headers).json()

    assert len(body) == 2  # bob の注文は入らない
    assert body[0]["id"] > body[1]["id"]  # 新しい注文が先
    assert [item["name"] for item in body[0]["items"]] == ["本0", "本1"]


@pytest.mark.parametrize("n_orders", [1, 5])
def test_query_count_does_not_grow(
    n_orders: int, user: User, auth_headers: dict[str, str], django_assert_num_queries
) -> None:
    make_orders(user, n_orders)

    # 身分証の確認1本 + 注文1本 + 明細と商品1本。注文が何件でも3本
    with django_assert_num_queries(3):
        client.get("/orders", headers=auth_headers)
