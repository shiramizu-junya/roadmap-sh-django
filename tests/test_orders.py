from decimal import Decimal

import pytest
from ninja.testing import TestClient

from accounts.models import User
from blog.models import Category
from config.api import api
from shop.models import Cart, CartItem, Inventory, Order, Product

client = TestClient(api)


@pytest.fixture
def book(db) -> Product:
    category = Category.objects.create(name="本")
    product = Product.objects.create(name="Django 入門", price=Decimal("2980"), category=category)
    Inventory.objects.create(product=product, quantity=5)
    return product


def put_in_cart(user: User, product: Product, quantity: int) -> None:
    cart, _ = Cart.objects.get_or_create(user=user)
    CartItem.objects.create(cart=cart, product=product, quantity=quantity)


def test_place_order(user: User, book: Product, auth_headers: dict[str, str]) -> None:
    put_in_cart(user, book, 2)

    res = client.post("/orders", headers=auth_headers)

    assert res.status_code == 201
    assert res.json()["total"] == "5960.00"
    assert Inventory.objects.get(product=book).quantity == 3  # 5 - 2
    assert CartItem.objects.count() == 0  # カートは空になる


def test_price_is_copied(user: User, book: Product, auth_headers: dict[str, str]) -> None:
    put_in_cart(user, book, 1)
    client.post("/orders", headers=auth_headers)

    book.price = Decimal("3500")  # 注文のあとで値上げ
    book.save()

    assert Order.objects.get().items.get().price == Decimal("2980")  # 注文の価格は変わらない


def test_out_of_stock_rolls_back(user: User, book: Product, auth_headers: dict[str, str]) -> None:
    put_in_cart(user, book, 6)  # 在庫は5

    res = client.post("/orders", headers=auth_headers)

    assert res.status_code == 409
    assert Order.objects.count() == 0  # 先に作った注文も取り消された
    assert CartItem.objects.count() == 1  # カートはそのまま


def test_last_one_is_sold_only_once(
    user: User, book: Product, auth_headers: dict[str, str]
) -> None:
    Inventory.objects.filter(product=book).update(quantity=1)  # 最後の1個
    bob = User.objects.create_user(username="bob", password="pass1234")
    put_in_cart(user, book, 1)
    put_in_cart(bob, book, 1)
    res = client.post("/auth/login", json={"username": "bob", "password": "pass1234"})
    bob_headers = {"Authorization": f"Bearer {res.json()['access']}"}

    assert client.post("/orders", headers=auth_headers).status_code == 201
    assert client.post("/orders", headers=bob_headers).status_code == 409  # 2人目は買えない
    assert Inventory.objects.get(product=book).quantity == 0  # マイナスにならない


def test_second_click_finds_empty_cart(
    user: User, book: Product, auth_headers: dict[str, str]
) -> None:
    put_in_cart(user, book, 1)

    assert client.post("/orders", headers=auth_headers).status_code == 201
    res = client.post("/orders", headers=auth_headers)  # もう一度押した

    assert res.status_code == 400  # カートはもう空
    assert Order.objects.count() == 1
    assert Inventory.objects.get(product=book).quantity == 4  # 1個だけ減る
