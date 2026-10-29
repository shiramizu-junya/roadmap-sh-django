from decimal import Decimal

import pytest
from ninja.testing import TestClient

from accounts.models import User
from config.api import api
from shop.models import Order

client = TestClient(api)


@pytest.fixture
def order(user: User) -> Order:
    return Order.objects.create(user=user, total=Decimal("2980"))


@pytest.fixture
def staff_headers(db) -> dict[str, str]:
    # お店の人（is_staff=True）の身分証
    User.objects.create_user(username="shop", password="pass1234", is_staff=True)
    res = client.post("/auth/login", json={"username": "shop", "password": "pass1234"})
    return {"Authorization": f"Bearer {res.json()['access']}"}


def test_cannot_skip_shipping(order: Order) -> None:
    # API を通さず、モデルのメソッドだけを試す
    with pytest.raises(ValueError):
        order.change_status(Order.Status.COMPLETED)  # 確定 → 完了 は飛ばしすぎ
    assert Order.objects.get(id=order.id).status == "placed"  # 台帳は変わっていない


def test_staff_ships_order(order: Order, staff_headers: dict[str, str]) -> None:
    res = client.patch(
        f"/orders/{order.id}/status", json={"status": "shipped"}, headers=staff_headers
    )

    assert res.status_code == 200
    assert res.json()["status"] == "shipped"


def test_cannot_go_back(order: Order, staff_headers: dict[str, str]) -> None:
    order.change_status(Order.Status.SHIPPED)

    res = client.patch(
        f"/orders/{order.id}/status", json={"status": "placed"}, headers=staff_headers
    )

    assert res.status_code == 409


def test_customer_cannot_change_status(order: Order, auth_headers: dict[str, str]) -> None:
    res = client.patch(
        f"/orders/{order.id}/status", json={"status": "shipped"}, headers=auth_headers
    )

    assert res.status_code == 403
