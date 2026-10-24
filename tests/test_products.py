from decimal import Decimal

import pytest
from django.db import IntegrityError
from ninja.testing import TestClient

from blog.models import Category
from config.api import api
from shop.models import Inventory, Product

client = TestClient(api)


@pytest.fixture
def product(db) -> Product:
    category = Category.objects.create(name="本")
    product = Product.objects.create(name="Django 入門", price=Decimal("2980"), category=category)
    Inventory.objects.create(product=product, quantity=5)
    return product


def test_list_products(product: Product) -> None:
    body = client.get("/products").json()
    assert body == [
        {
            "id": product.id,
            "name": "Django 入門",
            "price": "2980.00",  # 金額は文字列で返る
            "category_id": product.category_id,
            "stock": 5,
        }
    ]


def test_negative_stock_is_rejected_by_db(product: Product) -> None:
    # update() はモデルの検査を通らず、SQL をそのまま DB に送る
    with pytest.raises(IntegrityError):
        Inventory.objects.filter(product=product).update(quantity=-1)
