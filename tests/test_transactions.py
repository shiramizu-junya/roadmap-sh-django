import threading
from decimal import Decimal

import pytest
from django.db import connection
from ninja.testing import TestClient

from accounts.models import User
from blog.models import Category
from config.api import api
from shop.models import Cart, CartItem, Inventory, Order, Product

client = TestClient(api)


def login(username: str) -> dict[str, str]:
    User.objects.create_user(username=username, password="pass1234")
    res = client.post("/auth/login", json={"username": username, "password": "pass1234"})
    return {"Authorization": f"Bearer {res.json()['access']}"}


def post_at_the_same_time(url: str, headers_list: list[dict[str, str]]) -> list[int]:
    # 1人1スレッドで、同時に POST する。返すのはステータスコードの一覧
    statuses: list[int] = []
    start = threading.Barrier(len(headers_list))  # 全員そろってから、同時に走り出す

    def post(headers: dict[str, str]) -> None:
        start.wait()
        statuses.append(client.post(url, headers=headers).status_code)
        connection.close()  # このスレッドが開いた DB 接続を閉じる

    threads = [threading.Thread(target=post, args=(h,)) for h in headers_list]
    for t in threads:
        t.start()
    for t in threads:
        t.join()  # 全員終わるまで待つ
    return statuses


@pytest.mark.django_db(transaction=True)  # 本当に COMMIT する（テストの最後に全部消す）
def test_last_one_is_sold_once_even_at_the_same_time() -> None:
    category = Category.objects.create(name="本")
    book = Product.objects.create(name="Django 入門", price=Decimal("2980"), category=category)
    Inventory.objects.create(product=book, quantity=1)  # 最後の1個
    headers = [login("alice"), login("bob")]
    for user in User.objects.all():
        CartItem.objects.create(cart=Cart.objects.create(user=user), product=book, quantity=1)

    statuses = post_at_the_same_time("/orders", headers)

    assert sorted(statuses) == [201, 409]  # 1人だけ買える
    assert Order.objects.count() == 1
    assert Inventory.objects.get(product=book).quantity == 0
