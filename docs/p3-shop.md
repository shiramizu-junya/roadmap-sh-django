# 第3部 — EC 風に拡張する

> 第1部・第2部と同じく、1周目で全部分からなくて大丈夫です。
> 分からない箇所には `# TODO: わからん` と残して、先に進んでください。

---

## 第3部-1: 商品と在庫

**❓ この回の問い**: 第2部で、ブログ API はできあがった。ここに「物を売る」機能を足すと、記事には無かった何が要る？

**作るもの**: 新しい `shop` アプリ。商品・商品画像・在庫の3つの台帳と、商品の一覧・詳細 API
**重要度**: 🔴 毎日使う — お金と数量は、どの業務アプリにも出てくる
**前ステップとの接続**: 第2部のカテゴリ（`blog.Category`）を、商品の分類にも使い回す

### 1-0. このステップの初出

**Django / Ninja**: `DecimalField`, `CheckConstraint` / **Python**: `Decimal`

> 🧒 **かみくだくと**: **DecimalField** は、お金のための数の項目。小数を「10進数のまま」覚えるので、`0.1 + 0.2` が `0.3` からずれない。

> 🧒 **かみくだくと**: **CheckConstraint**（チェック制約）は、台帳そのものに貼る決まり。「在庫は0以上」と書いておくと、決まりを破る書き込みを **DB が** 断る。

### 1-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

**① アプリを作って登録する**（1-1 と同じ手順）

```bash
uv run python manage.py startapp shop
```

`config/settings.py` の `INSTALLED_APPS` に1行足す（`"blog",` の下）

```python
    "shop",  # 追加: shop アプリを登録する
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17

> 💡補足: `startapp` が作る `shop/apps.py` は、文字列が `'shop'`（シングルクォート）。コミットすると pre-commit の ruff が `"shop"` に直して、コミットが一度止まる。`git add` し直して、もう一度コミットすれば通る。

**② モデルを書く**（`shop/models.py` を全文置き換え）

```python
from django.db import models
from django.db.models import Q

from blog.models import Category


class Product(models.Model):
    name = models.CharField(max_length=100)
    # お金は小数の誤差が出ない DecimalField。全体で10桁、そのうち小数点以下が2桁
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # 多対一: 第2部のカテゴリを使い回す。商品が残っているカテゴリは消せない
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # 価格は0以上。破ろうとすると、DB が保存を断る
            models.CheckConstraint(condition=Q(price__gte=0), name="shop_product_price_gte_0"),
        ]

    def __str__(self) -> str:
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")

    def __str__(self) -> str:
        return self.image.name


class Inventory(models.Model):
    # 一対一: 1つの商品に、在庫の行は1つ
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="inventory")
    quantity = models.IntegerField(default=0)  # 在庫の数

    class Meta:
        constraints = [
            # 在庫は0以上。マイナスの在庫は、DB が保存を断る
            models.CheckConstraint(
                condition=Q(quantity__gte=0), name="shop_inventory_quantity_gte_0"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product.name}: {self.quantity}"
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17（ruff・mypy も通過）

> 💡補足: 制約の名前（`name=`）は、MySQL では**データベース全体で**重ならない名前にする決まりがある。だから頭に `shop_product_` のようにアプリ名とモデル名を付けている。

`shop/admin.py` を全文置き換え（データを見るための窓。学習対象ではない）

```python
from django.contrib import admin

from .models import Inventory, Product, ProductImage

# データを見るための窓（見た目の調整はしない）
admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(Inventory)
```

✅ 検証済み: Django 5.2.17

```bash
uv run python manage.py makemigrations shop
SQL_LOG=0 uv run python manage.py sqlmigrate shop 0001
uv run python manage.py migrate
```

```sql
CREATE TABLE `shop_product` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `name` varchar(100) NOT NULL, `price` numeric(10, 2) NOT NULL, `created_at` datetime(6) NOT NULL, `category_id` bigint NOT NULL);
CREATE TABLE `shop_inventory` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `quantity` integer NOT NULL, `product_id` bigint NOT NULL UNIQUE);
-- （shop_productimage は 2-10 の PostImage と同じ形なので省略）
ALTER TABLE `shop_product` ADD CONSTRAINT `shop_product_price_gte_0` CHECK (`price` >= 0);
ALTER TABLE `shop_inventory` ADD CONSTRAINT `shop_inventory_quantity_gte_0` CHECK (`quantity` >= 0);
```

✅ 検証済み: MySQL 8.4.11（外部キーの `ALTER TABLE` 3行も続けて出る）

**③ API を書く**（`shop/api.py` 新規）

```python
from decimal import Decimal

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Field, Router, Schema

from .models import Product

# 商品の API 一式。URL の頭（/products）は config/api.py で決める
router = Router()


class ProductOut(Schema):
    id: int
    name: str
    price: Decimal  # 金額。JSON では "1200.00" のような文字列になる
    category_id: int
    stock: int = Field(alias="inventory.quantity")  # 在庫の数（一対一の先をたどる）


@router.get("", response=list[ProductOut])
def list_products(request: HttpRequest):
    # 在庫は一対一なので、JOIN で同じ SQL に入れる
    return Product.objects.select_related("inventory").order_by("id")


@router.get("/{product_id}", response=ProductOut)
def get_product(request: HttpRequest, product_id: int):
    return get_object_or_404(Product.objects.select_related("inventory"), id=product_id)
```

✅ 検証済み: django-ninja 1.7.1（ruff・mypy も通過）

`config/api.py` に2行足す（import は `blog.api` の下、`add_router` は最後）

```python
from shop.api import router as products_router
```

```python
api.add_router("/products", products_router, tags=["products"])
```

✅ 検証済み: django-ninja 1.7.1

**④ 試す**

管理画面（`/admin/`）の Products で商品を2つ作り、Inventorys でそれぞれに在庫の行を作ります（1つは在庫 `0`）。

```bash
curl -s http://127.0.0.1:8000/api/products
```

```text
[{"id": 1, "name": "Django 入門", "price": "2980.00", "category_id": 1, "stock": 5}, {"id": 2, "name": "Python ノート", "price": "450.50", "category_id": 1, "stock": 0}]
```

✅ 検証済み: 実際の出力は日本語が `入` のような形になる。読みやすくするため戻して載せた

続けて、管理画面で在庫を `-1` に書き換えて保存してみてください。保存されずに、次の文が出ます。

```text
Constraint “shop_inventory_quantity_gte_0” is violated.
```

✅ 検証済み: Django 5.2.17（`full_clean()` の結果で確認）

**⑤ テスト**（`tests/test_products.py` 新規）

```python
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
```

✅ 検証済み: pytest-django 4.14.0（`40 passed`。ruff・mypy も通過）

### 1-2. 🔬 仕組み解剖

| | `DecimalField` | `CheckConstraint` |
| --- | --- | --- |
| 正式名称 | DecimalField（`max_digits`・`decimal_places`） | CheckConstraint（`Meta.constraints` に書く） |
| いつ・誰が | 読むときに Django が、DB の値を Python の `Decimal` にする。API の返事では、Django の JSON 変換が文字列にする | `migrate` のときに `ADD CONSTRAINT ... CHECK` が流れる。以降は**書き込みのたびに MySQL が**調べる |
| 発行される SQL | `price numeric(10, 2)` | `CHECK (quantity >= 0)` |
| TS での対応物 | 対応物なし。JS の数は小数を2進数で持つので、`0.1 + 0.2` がずれる | 対応物なし（DB の機能）。Zod の `.min(0)` に似るが、あちらはアプリの中だけで効く |
| なぜこの設計 | 金額のずれは「1円合わない」事故になる。数字で返すと、受け取った側の JS が小数を丸めかねない | アプリの検査は、`update()` や手で打った SQL では通らない。DB に貼れば、どこから書いても守られる |
| 失敗すると | 桁あふれ（11桁）は管理画面で入力エラー。`create()` なら MySQL が `DataError`（1264 Out of range）で断る | 管理画面は保存前に気づいて入力エラーにする（`full_clean()`）。`update()` なら `IntegrityError`（3819）。API の中なら 500 |

✅ 検証済み: Django 5.2.17 / MySQL 8.4.11（「失敗すると」はすべて、わざと起こして確認）

```text
  blog_category
       ^
       | many-to-one (PROTECT)
       |
  shop_product  <------ shop_productimage   (many images per product)
       ^
       | one-to-one (UNIQUE)
       |
  shop_inventory   CHECK (quantity >= 0)
```

✅ 検証済み: ②のモデルと 0001 のマイグレーション

見てほしいのは、在庫が商品の台帳とは**別の台帳**になっている点です。第3部-4 で、在庫の行だけを書き換える話が出てきます。

### 1-3. 🐍 Python注

> 🐍 **Python注**: `Decimal("2980")` は標準の `decimal` モジュールの10進数。必ず**文字列から**作る。
> `Decimal(0.1)` と小数から作ると、2進数のずれまで写してしまう。

### 1-4. 解説 — なぜこう設計するか

在庫を Product の項目にせず、一対一の別の台帳にしました。商品名を直す人と、在庫を減らす注文の処理は、別々のときに動きます。在庫の行が分かれていれば、注文の処理は在庫の行だけを押さえれば済みます。

🧠 Django の考え方: 入口の検査（スキーマ）と、台帳の決まり（制約）は、別の層の仕事。大事な決まりは、最後の砦である DB にも書く。

### 1-5. ⚠️ アンチパターン

> ⚠️ **アンチパターン**: 金額を `FloatField` にする。`FloatField` は2進数の小数（`float`）で持つので、足し算を重ねると端数がずれる。Django の公式ドキュメントも、2つの違いを分けて説明している。
> 根拠: https://docs.djangoproject.com/en/5.2/ref/models/fields/#floatfield-vs-decimalfield

### 1-6. 🔮 予測 → 動作確認

1. 管理画面で、在庫の行を**作らない**商品を1つ足した。`GET /api/products` はどうなる？ `GET /api/products/1`（在庫ありの商品）は？
2. `price` に `Decimal("1.005")` を入れて保存し、読み直すと何になる？
3. 価格に `123456789.00`（11桁）を入れて `Product.objects.create()` すると？

<details><summary>答え</summary>

1. 一覧は **500**。在庫の行が無い商品で `inventory.quantity` をたどれず、返事の検査（`Field required`）で止まる。1件の不備で一覧全体が落ちる。詳細の 1 は 200 のまま（検証済み）
2. `1.01`。小数点以下2桁に丸めて保存される（検証済み）
3. MySQL が `DataError`（1264 Out of range value for column 'price'）で断る（検証済み）

</details>

1 から分かるのは、商品を作ったら在庫の行も必ず作る、という約束が要ることです。

### 1-7. ✅ 想起チェック

1. `max_digits=10, decimal_places=2` で、整数部分は何桁まで入る？
2. `update()` で在庫を `-1` にすると、誰が、何というエラーで断る？

<details><summary>答え</summary>

1. 8桁（全体10桁から、小数点以下の2桁を引く）
2. MySQL が断り、Django が `IntegrityError` にして投げる。モデルの検査（`full_clean()`）は通らない

</details>

### 1-8. 📇 まとめカード

この回で覚えることは1つだけ: **お金は `DecimalField`。「0以上」のような必ず守る決まりは、`CheckConstraint` で DB に貼る。**

📒 用語集に追記: `DecimalField` / `Decimal` / `CheckConstraint`（チェック制約） / `IntegrityError`

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第3部 ステップ2` — カート


---

## 第3部-2: カート

**❓ この回の問い**: 3-1 で商品と在庫ができた。買う前に「カートに入れる」とき、同じ商品を2回入れたら、行は2つになる？

**作るもの**: `POST /api/cart/items`（カートに入れる）と `GET /api/cart`（中身と合計金額）
**重要度**: 🔴 毎日使う — 「無ければ作る、あれば足す」は、カート以外でもよく出る形
**前ステップとの接続**: 3-1 の Product を、ログイン中の人のカートに入れる（ログインは 2-6 の `JWTAuth`）

### 2-0. このステップの初出

**Django / Ninja**: `UniqueConstraint`, `get_or_create()` / **Python**: `a, b = ...`（分けて受け取る）

> 🧒 **かみくだくと**: **UniqueConstraint**（一意制約）は、「この組み合わせの行は1つだけ」という台帳の決まり。ここでは「同じカートに、同じ商品の行は1つ」。

> 🧒 **かみくだくと**: **get_or_create()** は、「台帳を探して、無ければその場で作る」を1回で頼む命令。見つかったのか作ったのかも教えてくれる。

### 2-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

**① モデルを書く**（`shop/models.py`）

import を1行足す（`from django.db import models` の**上**）

```python
from django.conf import settings
```

✅ 検証済み: ruff の import 順チェックも通過

ファイルの**最後**（`class Inventory` の下）に追加

```python
class Cart(models.Model):
    # 一対一: 1人に、カートは1つ
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user_id} のカート"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()  # カートに入れた数

    class Meta:
        constraints = [
            # 同じカートに、同じ商品の行は1つだけ（2回入れたら数を足す）
            models.UniqueConstraint(
                fields=["cart", "product"], name="shop_cartitem_unique_cart_product"
            ),
            # 数は1以上
            models.CheckConstraint(
                condition=Q(quantity__gte=1), name="shop_cartitem_quantity_gte_1"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product.name} x {self.quantity}"
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17（ruff・mypy も通過）

`shop/admin.py` は、import の1行を置き換え、最後に2行足す

```python
from .models import Cart, CartItem, Inventory, Product, ProductImage
```

```python
admin.site.register(Cart)
admin.site.register(CartItem)
```

✅ 検証済み: Django 5.2.17

```bash
uv run python manage.py makemigrations shop
SQL_LOG=0 uv run python manage.py sqlmigrate shop 0002
uv run python manage.py migrate
```

```sql
CREATE TABLE `shop_cart` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `created_at` datetime(6) NOT NULL, `user_id` bigint NOT NULL UNIQUE);
CREATE TABLE `shop_cartitem` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `quantity` integer NOT NULL, `cart_id` bigint NOT NULL, `product_id` bigint NOT NULL, CONSTRAINT `shop_cartitem_unique_cart_product` UNIQUE (`cart_id`, `product_id`), CONSTRAINT `shop_cartitem_quantity_gte_1` CHECK (`quantity` >= 1));
```

✅ 検証済み: MySQL 8.4.11（外部キーの `ALTER TABLE` 3行も続けて出る）

`shop_cart` の `user_id` は1列だけの `UNIQUE`（一対一）。`shop_cartitem` は、**2列の組み合わせ**で `UNIQUE` です。

**② API を書く**（`shop/api.py`）

`from ninja import ...` から `from .models import Product` までの3行（空行を含む）を、次の4行に置き換える

```python
from ninja import Field, Router, Schema, Status
from ninja_jwt.authentication import JWTAuth

from .models import Cart, CartItem, Product
```

✅ 検証済み: ruff の import 順チェックも通過

ファイルの**最後**（`get_product` の下）に追加

```python
# カートの API 一式。URL の頭（/cart）は config/api.py で決める
cart_router = Router()


class CartItemIn(Schema):
    product_id: int
    quantity: int = Field(default=1, ge=1)  # 省略したら1個。0以下は 422


class CartItemOut(Schema):
    product_id: int
    name: str = Field(alias="product.name")
    price: Decimal = Field(alias="product.price")
    quantity: int


class CartOut(Schema):
    items: list[CartItemOut]
    total: Decimal  # 合計金額


@cart_router.post("/items", response={201: CartItemOut}, auth=JWTAuth())
def add_to_cart(request: HttpRequest, payload: CartItemIn):
    product = get_object_or_404(Product, id=payload.product_id)
    assert request.user.is_authenticated
    # 自分のカートを取る。無ければ作る
    cart, _ = Cart.objects.get_or_create(user=request.user)
    # 同じ商品の行を取る。無ければ、入れた数で作る
    item, created = CartItem.objects.get_or_create(
        cart=cart, product=product, defaults={"quantity": payload.quantity}
    )
    if not created:
        # もう入っていたら、行は増やさずに数を足す
        item.quantity += payload.quantity
        item.save()
    return Status(201, item)


@cart_router.get("", response=CartOut, auth=JWTAuth())
def get_cart(request: HttpRequest):
    assert request.user.is_authenticated
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related("product").order_by("id")
    total = sum((item.product.price * item.quantity for item in items), Decimal("0"))
    return {"items": items, "total": total}
```

✅ 検証済み: django-ninja 1.7.1（ruff・mypy も通過）

`config/api.py` に2行足す（import は `from shop.api import router ...` の**上**、`add_router` は最後）

```python
from shop.api import cart_router
```

```python
api.add_router("/cart", cart_router, tags=["cart"])
```

✅ 検証済み: django-ninja 1.7.1（ruff の import 順チェックも通過）

**③ 試す**（`ACCESS` は 2-6 の手順で入れ直す。商品の id は 3-1 で作ったもの）

```bash
curl -s -X POST http://127.0.0.1:8000/api/cart/items -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" -d '{"product_id": 1}'
curl -s -X POST http://127.0.0.1:8000/api/cart/items -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" -d '{"product_id": 1, "quantity": 2}'
curl -s -X POST http://127.0.0.1:8000/api/cart/items -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" -d '{"product_id": 2}'
curl -s http://127.0.0.1:8000/api/cart -H "Authorization: Bearer $ACCESS"
```

```text
{"product_id": 1, "name": "Django 入門", "price": "2980.00", "quantity": 1}
{"product_id": 1, "name": "Django 入門", "price": "2980.00", "quantity": 3}
{"product_id": 2, "name": "Python ノート", "price": "450.50", "quantity": 1}
{"items": [{"product_id": 1, "name": "Django 入門", "price": "2980.00", "quantity": 3}, {"product_id": 2, "name": "Python ノート", "price": "450.50", "quantity": 1}], "total": "9390.50"}
```

✅ 検証済み: 2回目は行が増えずに `3` になる（日本語は読みやすく戻して載せた）

1回目のログに出る SQL です（カートも行も、まだ無いとき）。

```sql
SELECT ... FROM `shop_cart` WHERE `shop_cart`.`user_id` = 2 LIMIT 21;
BEGIN;
INSERT INTO `shop_cart` (`user_id`, `created_at`) VALUES (2, '2026-10-24 08:45:26.800703');
COMMIT;
SELECT ... FROM `shop_cartitem` WHERE (`shop_cartitem`.`cart_id` = 2 AND `shop_cartitem`.`product_id` = 1) LIMIT 21;
BEGIN;
INSERT INTO `shop_cartitem` (`cart_id`, `product_id`, `quantity`) VALUES (2, 1, 1);
COMMIT;
```

✅ 検証済み: MySQL 8.4.11（開発サーバの SQL ログ。列名は `...` に縮めた）

**④ テスト**（`tests/test_cart.py` 新規）

要件だけ書きます（`user`・`auth_headers` は 2-6 の `conftest.py` のもの）。

1. 同じ商品を「1個」「2個」と2回入れると、201 で数は `3`。`CartItem` の行は1つのまま
2. 2個入れて `GET /cart` すると、`items` に1行、`total` は `"5960.00"`
3. 身分証なしの `GET /cart` は 401

<details><summary>解答例</summary>

```python
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
```

</details>

✅ 検証済み: pytest-django 4.14.0（`43 passed`。ruff・mypy も通過）

### 2-2. 🔬 仕組み解剖

| | `UniqueConstraint` | `get_or_create()` |
| --- | --- | --- |
| 正式名称 | UniqueConstraint（`Meta.constraints` に書く） | QuerySet.get_or_create() |
| いつ・誰が | `migrate` で `UNIQUE (cart_id, product_id)` が貼られる。以降は書き込みのたびに MySQL が調べる | 呼ぶたびに Django が `SELECT` する。無ければ `INSERT` する。戻り値は `(行, 作ったか)` の2つ組 |
| 発行される SQL | `CONSTRAINT ... UNIQUE (cart_id, product_id)` | ③の SQL。見つかったときは `SELECT` 1本だけ |
| TS での対応物 | 対応物なし（DB の機能） | 対応物なし。Prisma の `upsert` が近いが、あちらは「あれば更新」までする |
| なぜこの設計 | 「1つだけ」をアプリで確かめても、同時に来た2つのリクエストは両方「無い」と見る。DB の決まりなら必ず1つで止まる | 「探す → 無ければ作る」を毎回 `if` で書かずに済む。同時に作られたときも、一意制約にぶつかったら探し直してくれる |
| 失敗すると | 同じ組を `create()` すると `IntegrityError`（1062 Duplicate entry '1-1'）。API の中なら 500 | 一意の決まりが無い項目で使うと、同時に2行できることがある。2行になると、次から `MultipleObjectsReturned`（500） |

✅ 検証済み: Django 5.2.17 / MySQL 8.4.11（「失敗すると」の 1062 はわざと起こして確認）

```text
  get_or_create(cart=cart, product=product, defaults={"quantity": 1})
                 |
                 v
        SELECT ... WHERE cart_id = ? AND product_id = ?
                 |
        found? --+-- yes --> (item, False) --> quantity += n --> UPDATE
                 |
                 no
                 |
                 v
        INSERT (cart_id, product_id, quantity=1) --> (item, True)
```

✅ 検証済み: ③の SQL ログと、2回目の `UPDATE`

見てほしいのは、`defaults` が**作るときだけ**使われる点です。見つかったときは使われないので、数を足す処理は自分で書いています。

### 2-3. 🐍 Python注

> 🐍 **Python注**: `item, created = ...` は、2つ組の戻り値を2つの変数に分けて受け取る書き方（TS の `const [item, created] = ...`）。
> 使わない方は `_` という名前で受けて、「使わない」と示す。

### 2-4. 解説 — なぜこう設計するか

カートは「1人に1つ」なので一対一、カートの中身は「1カートに同じ商品1行」なので2列の一意制約にしました。どちらも、決まりを台帳に書いています。アプリのコードがどう変わっても、DB が最後に守ります。

🧠 Django の考え方: 「1つだけ」は、アプリの `if` ではなく台帳の決まりで守る。`get_or_create()` は、その決まりがあって初めて安全になる。

> ⏭️ **後で回収**: `item.quantity += ...` → `save()` は、「読んで、足して、書く」の3手。2つのリクエストが同時にこれをすると、片方の足し算が消えることがある。第3部-4（`F()` 式）で、実際に起こして直す。

### 2-5. ⚠️ アンチパターン

> ⚠️ **アンチパターン**: 組み合わせの一意を、古い書き方の `unique_together` で書く。Django の公式ドキュメントは `UniqueConstraint` を使うよう勧めており、`unique_together` は将来なくなるかもしれないと書いている。
> 根拠: https://docs.djangoproject.com/en/5.2/ref/models/options/#unique-together

### 2-6. 🔮 予測 → 動作確認

1. 同じ商品を2回入れたとき、2回目に流れる SQL は？ `INSERT` は出る？
2. `{"product_id": 1, "quantity": 0}` を送ると？ DB の `CHECK` まで届く？
3. shell で、もう入っている組み合わせを `CartItem.objects.create(...)` したら？

<details><summary>答え</summary>

1. `INSERT` は出ない。`SELECT`（見つかった）→ `UPDATE ... SET quantity = 3` になる（検証済み）
2. 届かない。スキーマの `ge=1` で止まり、422（`Input should be greater than or equal to 1`）。DB の `CHECK` は、スキーマを通らない書き込みのための砦（検証済み）
3. `IntegrityError: (1062, "Duplicate entry '1-1' for key 'shop_cartitem.shop_cartitem_unique_cart_product'")`（検証済み）

</details>

### 2-7. ✅ 想起チェック

1. `get_or_create()` の戻り値の2つめは何？
2. `defaults=` に書いた値は、どんなときに使われる？

<details><summary>答え</summary>

1. 今作ったかどうか（`True` なら作った、`False` なら見つかった）
2. 見つからずに、新しく作るときだけ

</details>

### 2-8. 📇 まとめカード

この回で覚えることは1つだけ: **「1つだけ」は `UniqueConstraint` で台帳に書き、`get_or_create()` で「無ければ作る」。**

📒 用語集に追記: `UniqueConstraint`（一意制約） / `get_or_create()` / `defaults`

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第3部 ステップ3` — 注文を確定する


---

## 第3部-3: 注文を確定する

**❓ この回の問い**: 3-2 でカートができた。「注文する」は、注文を作る・明細を作る・在庫を減らす・カートを空にする、の4手。3手目で失敗したら、1手目と2手目はどうなる？

**作るもの**: `POST /api/orders`。カートの中身を注文にし、買った時点の価格を明細に写して、在庫を減らす
**重要度**: 🔴 毎日使う — 「いくつも書き込む処理」は、ほぼ必ずトランザクションで包む
**前ステップとの接続**: 3-2 のカートを注文に変える。2-8 で先送りにした「User と Profile を別々に INSERT」も、ここで直す

### 3-0. このステップの初出

**Django / Ninja**: `transaction.atomic`, `bulk_create()` / **Python**: `with`

> 🧒 **かみくだくと**: **トランザクション**（transaction）は、いくつもの書き込みを「全部やるか、何もしないか」の1かたまりにすること。台帳の書き換えを、最後にまとめて「確定」（コミット）する。途中で失敗したら「取り消し」（ロールバック）で、始める前の台帳に戻る。

> 🧒 **かみくだくと**: **bulk_create()** は、何行もの INSERT を **SQL 1本**にまとめて送る命令。

### 3-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

**① モデルを書く**（`shop/models.py` の**最後**に追加）

```python
class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    total = models.DecimalField(max_digits=12, decimal_places=2)  # 合計金額（確定した時点）
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"注文 {self.id}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    # 注文の記録が残っている商品は消せない
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    # 買った時点の価格を写しておく。あとで商品の価格が変わっても、注文の金額は変わらない
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()

    def __str__(self) -> str:
        return f"{self.product.name} x {self.quantity}"
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17（ruff・mypy も通過）

`shop/admin.py` は、import の1行を置き換え、最後に2行足す

```python
from .models import Cart, CartItem, Inventory, Order, OrderItem, Product, ProductImage
```

```python
admin.site.register(Order)
admin.site.register(OrderItem)
```

✅ 検証済み: Django 5.2.17

```bash
uv run python manage.py makemigrations shop
uv run python manage.py migrate
```

✅ 検証済み: `shop/migrations/0003_order_orderitem.py` ができ、`shop_order`・`shop_orderitem` の2つの台帳ができる

> 💡補足: `Order.user` は `PROTECT` にしました。注文の記録は、お金の記録です。ユーザーを消しても、注文が一緒に消えてはいけません。

**② API を書く**（`shop/api.py`）

import の行を、次のように直す（3か所）

```diff
+from datetime import datetime
 from decimal import Decimal

+from django.db import transaction
 from django.http import HttpRequest
```

```diff
 from ninja import Field, Router, Schema, Status
+from ninja.errors import HttpError
 from ninja_jwt.authentication import JWTAuth
```

```diff
-from .models import Cart, CartItem, Product
+from .models import Cart, CartItem, Order, OrderItem, Product
```

✅ 検証済み: ruff の import 順チェックも通過

ファイルの**最後**（`get_cart` の下）に追加

```python
# 注文の API 一式。URL の頭（/orders）は config/api.py で決める
order_router = Router()


class OrderItemOut(Schema):
    product_id: int
    price: Decimal  # 買った時点の価格
    quantity: int


class OrderOut(Schema):
    id: int
    total: Decimal
    created_at: datetime
    items: list[OrderItemOut]


@order_router.post("", response={201: OrderOut}, auth=JWTAuth())
def place_order(request: HttpRequest):
    assert request.user.is_authenticated
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = list(cart.items.select_related("product__inventory"))
    if not cart_items:
        raise HttpError(400, "カートが空です")

    # ここから下は「全部やるか、何もしないか」。途中で例外が出たら、全部取り消す
    with transaction.atomic():
        total = sum((ci.product.price * ci.quantity for ci in cart_items), Decimal("0"))
        order = Order.objects.create(user=request.user, total=total)
        # 注文の明細を、INSERT 1本でまとめて作る
        OrderItem.objects.bulk_create(
            [
                OrderItem(
                    order=order, product=ci.product, price=ci.product.price, quantity=ci.quantity
                )
                for ci in cart_items
            ]
        )
        for ci in cart_items:
            inventory = ci.product.inventory
            if inventory.quantity < ci.quantity:
                # 例外で with を抜けると、上で作った注文と明細も無かったことになる
                raise HttpError(409, f"「{ci.product.name}」の在庫が足りません")
            inventory.quantity -= ci.quantity
            inventory.save()
        cart.items.all().delete()  # カートを空にする

    return Status(201, order)
```

✅ 検証済み: django-ninja 1.7.1（ruff・mypy も通過）

> 💡補足: `select_related("product__inventory")` の `__` は、2-11 と同じ「リレーションの先をたどる」印。カートの行 → 商品 → 在庫まで、JOIN で1本の SQL に入れる。

`config/api.py` は、`cart_router` の import に `order_router` を足し、最後に1行足す

```diff
-from shop.api import cart_router
+from shop.api import cart_router, order_router
```

```python
api.add_router("/orders", order_router, tags=["orders"])
```

✅ 検証済み: django-ninja 1.7.1

**③ 2-8 の宿題を直す**（`accounts/api.py`）

import を1行足す（`from django.contrib.auth import authenticate` の下）

```python
from django.db import transaction
```

`register` の中の、`create_user` と `Profile.objects.create` の3行を置き換える

```python
    # User と Profile は両方できるか、両方できないか（片方だけ残さない）
    with transaction.atomic():
        # create_user: パスワードをハッシュにしてから保存する
        user = User.objects.create_user(username=payload.username, password=payload.password)
        Profile.objects.create(user=user)  # 空のプロフィールを一緒に作る
```

✅ 検証済み: Django 5.2.17（2-8 のテストは何も変えずに通る）

これで 2-8 の ⏭️ を回収しました。Profile の INSERT が失敗すると、User の INSERT も取り消されます。

**④ 試す**（在庫は、商品 1 が `5`、商品 2 が `0`。`ACCESS` は入れ直す）

```bash
curl -s -X POST http://127.0.0.1:8000/api/cart/items -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" -d '{"product_id": 1, "quantity": 2}'
curl -s -X POST http://127.0.0.1:8000/api/cart/items -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" -d '{"product_id": 2}'
curl -s -w " %{http_code}\n" -X POST http://127.0.0.1:8000/api/orders -H "Authorization: Bearer $ACCESS"
```

```text
{"detail": "「Python ノート」の在庫が足りません"} 409
```

✅ 検証済み: 管理画面で見ると、Orders は0件。商品 1 の在庫も `5` のまま

ログの SQL です。注文と明細の INSERT、在庫の UPDATE まで進んでから、**`ROLLBACK`** で全部取り消しています。

```sql
BEGIN;
INSERT INTO `shop_order` (`user_id`, `total`, `created_at`) VALUES (1, 6410.50, '2026-10-25 04:20:07.679768');
INSERT INTO `shop_orderitem` (`order_id`, `product_id`, `price`, `quantity`) VALUES (1, 1, 2980.00, 2), (1, 2, 450.50, 1);
UPDATE `shop_inventory` SET `product_id` = 1, `quantity` = 3 WHERE `shop_inventory`.`id` = 1;
ROLLBACK;
```

✅ 検証済み: MySQL 8.4.11（開発サーバの SQL ログ）

管理画面の Cart items で商品 2 の行を消してから、もう一度注文します。

```bash
curl -s -w " %{http_code}\n" -X POST http://127.0.0.1:8000/api/orders -H "Authorization: Bearer $ACCESS"
```

```text
{"id": 2, "total": "5960.00", "created_at": "2026-10-25T04:20:08.957Z", "items": [{"product_id": 1, "price": "2980.00", "quantity": 2}]} 201
```

```sql
BEGIN;
INSERT INTO `shop_order` (`user_id`, `total`, `created_at`) VALUES (1, 5960.00, '2026-10-25 04:20:08.957161');
INSERT INTO `shop_orderitem` (`order_id`, `product_id`, `price`, `quantity`) VALUES (2, 1, 2980.00, 2);
UPDATE `shop_inventory` SET `product_id` = 1, `quantity` = 3 WHERE `shop_inventory`.`id` = 1;
DELETE FROM `shop_cartitem` WHERE `shop_cartitem`.`cart_id` = 1;
COMMIT;
```

✅ 検証済み: MySQL 8.4.11（在庫は `3`、カートは空。注文の id が `2` なのは 🔮 の 3 で）

**⑤ テスト**（`tests/test_orders.py` 新規）

要件だけ書きます（`user`・`auth_headers` は `conftest.py` のもの）。

1. 在庫5の商品を2個カートに入れて注文すると、201 で `total` は `"5960.00"`。在庫は `3`、カートは空
2. 注文のあとで商品を値上げしても、明細の `price` は注文した時点の `2980` のまま
3. 在庫5の商品を6個入れて注文すると、409。注文は0件で、カートの行は残る

<details><summary>解答例</summary>

```python
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
```

</details>

✅ 検証済み: pytest-django 4.14.0（`46 passed`。ruff・mypy も通過）

### 3-2. 🔬 仕組み解剖

| | `transaction.atomic` | `bulk_create()` |
| --- | --- | --- |
| 正式名称 | django.db.transaction.atomic | QuerySet.bulk_create() |
| いつ・誰が | `with` に入るときに Django が `BEGIN` を送る。ふつうに抜けたら `COMMIT`、例外で抜けたら `ROLLBACK`。取り消すのは MySQL | 呼んだときに Django が、全部の行を `VALUES (...), (...)` の INSERT 1本にする |
| 発行される SQL | `BEGIN` … `COMMIT` ／ `ROLLBACK` | `INSERT INTO shop_orderitem ... VALUES (1, 1, ...), (1, 2, ...)` |
| TS での対応物 | 対応物なし（DB の機能）。Prisma の `$transaction` が同じ役目 | 対応物なし（ORM の機能）。Prisma の `createMany` が同じ役目 |
| なぜこの設計 | Django は、ふだん1本ごとに確定する（自動コミット）。何本かを1かたまりにしたいところだけ、自分で囲む | 明細が10行なら、`create()` では SQL が10本。まとめれば1本で済む |
| 失敗すると | `with` を書き忘れると、409 を返しても**注文の行は残る**（わざと外して確認）。例外を `with` の**中で** `try` して握りつぶすと、取り消されない | 行ごとの `save()` を通らない。MySQL では、作った行に `id` が入らない（`None`。確認済み） |

✅ 検証済み: Django 5.2.17 / MySQL 8.4.11

```text
  POST /api/orders
     |
     v
  read cart (SELECT)
     |
     v
  +--------- transaction.atomic() ----------+
  | BEGIN                                   |
  | INSERT order                            |
  | INSERT order items (bulk_create)        |
  | UPDATE inventory  -- not enough? -> 409 |---> ROLLBACK (all undone)
  | DELETE cart items                       |
  | COMMIT                                  |
  +-----------------------------------------+
     |
     v
  201
```

✅ 検証済み: ④の SQL ログ

見てほしいのは、枠の中のどこで例外が出ても、出口が `ROLLBACK` の1本しかない点です。

### 3-3. 🐍 Python注

> 🐍 **Python注**: `with A:` は、「中に入るときに A の準備を、出るときに A の後片付けを必ずする」書き方。例外で出るときも、後片付けは必ず走る。
> `transaction.atomic()` は、出るときの後片付けで `COMMIT` か `ROLLBACK` を選ぶ。

### 3-4. 解説 — なぜこう設計するか

明細には、商品の価格を**写して**持たせました。商品を指すだけにすると、値上げした日に、過去の注文の金額まで変わってしまいます。注文は「その時点の記録」なので、変わってはいけない値は写しておきます。

🧠 Django の考え方: Django はふだん1本ずつ確定する。「全部か、何もしないか」にしたい範囲は、自分で `atomic` で囲む。

> ⏭️ **後で回収**: 在庫の `inventory.quantity -= ...` → `save()` は、3-2 のカートと同じ「読んで、足して、書く」。最後の1個を2人が同時に注文すると、2人とも買えてしまう。トランザクションだけでは防げない。第3部-4 で実際に起こし、3-4・3-5 で直す。

### 3-5. 🏢 実務メモ

> 🏢 **実務メモ**: 設定 `ATOMIC_REQUESTS = True` にすると、全部のリクエストを丸ごと1つのトランザクションで包める。ただし公式ドキュメントは、アクセスが増えると効率が落ちると注意している。この教材では、要るところだけ `atomic` で囲む。
> 根拠: https://docs.djangoproject.com/en/5.2/topics/db/transactions/#tying-transactions-to-http-requests

### 3-6. 🔮 予測 → 動作確認

1. `place_order` から `with transaction.atomic():` を外して（中身は1段浅くして）、在庫の足りない注文を送ると？ ステータスコードと、Orders の件数は？
2. カートが空のまま `POST /api/orders` すると？ カート自体がまだ無い人なら？
3. ④で、2回目に成功した注文の id は `2` だった。注文は1件しか無いのに、なぜ `1` ではない？

<details><summary>答え</summary>

1. ステータスは同じ 409。でも Orders に1件、明細に2件が**残る**。在庫も1つ目の商品だけ減ったまま。1本ずつ確定してしまうから（検証済み）
2. 空なら 400（`カートが空です`）。カートが無い人は、`get_object_or_404` で 404（検証済み）
3. 取り消された1回目が、id の `1` を使ったから。MySQL の `AUTO_INCREMENT` の番号は、`ROLLBACK` しても戻らない（検証済み）

</details>

### 3-7. ✅ 想起チェック

1. `with transaction.atomic():` の中で例外が出たら、Django は MySQL に何を送る？
2. 明細（OrderItem）に、商品の価格を写して持たせるのはなぜ？

<details><summary>答え</summary>

1. `ROLLBACK`。`BEGIN` からあとの書き込みが、全部無かったことになる
2. あとで商品の価格が変わっても、注文の金額を変えないため

</details>

### 3-8. 📇 まとめカード

この回で覚えることは1つだけ: **いくつも書き込む処理は `transaction.atomic()` で囲む。途中で例外が出れば、全部取り消される。**

📒 用語集に追記: トランザクション / `transaction.atomic` / コミット・ロールバック / `bulk_create()`

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第3部 ステップ4` — 同時に買うと壊れる


---

## 第3部-4: 同時に買うと壊れる

**❓ この回の問い**: 3-3 で、在庫が足りなければ注文を全部取り消せるようになった。では、最後の1個を2人が**同時に**注文したら？ トランザクションは守ってくれる？

**作るもの**: 「2人とも買えてしまう」を実際に起こす。`F()` 式で、在庫とカートの数を MySQL に計算させて直す
**重要度**: 🔴 毎日使う — 「読んで、計算して、書く」は、アクセスが重なると必ず壊れる
**前ステップとの接続**: 3-2 と 3-3 で宣言した ⏭️（カートの `+=`、在庫の `-=`）を、ここで回収する

### 4-0. このステップの初出

**Django / Ninja**: `F()` 式, `QuerySet.update()` / **Python**: なし

> 🧒 **かみくだくと**: **F() 式**（F expression）は、「台帳に今書いてある値」を指す印。`F("quantity") - 1` と書くと、Django は Python で引き算せずに、`quantity = quantity - 1` という SQL を MySQL に送る。引き算は MySQL が、その瞬間の値でやる。

> 🧒 **かみくだくと**: **update()** は、`filter()` で絞った行をまとめて書き換える命令。行を Python に読み込まずに、`UPDATE` 1本で済ませる。戻り値は、書き換えた行の数。

### 4-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

**① 壊れるのを見る**

同時に来た2つのリクエストを、確実に重ねるため、**一時的に** 1 秒待たせます（`shop/api.py`）。

ファイルの1行目に足す

```python
import time
```

`place_order` の `raise HttpError(400, "カートが空です")` の下に足す（`with` と同じ深さ）

```python
    time.sleep(1)  # 一時的: 2人が「在庫1」を読み終わるまで待つ
```

✅ 検証済み: Django 5.2.17（②のあとで消す）

管理画面で、商品 1 の Inventory の quantity を `1` にします。2人目の bob を登録し、2人とも商品 1 をカートに入れます。

```bash
# bob を登録する（2-8 の API）
curl -s -X POST http://127.0.0.1:8000/api/auth/register \
  -H "Content-Type: application/json" -d '{"username": "bob", "password": "pass1234"}'

# 2人の身分証を取る
ACCESS=$(curl -s -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "pass1234"}' \
  | uv run python -c "import json, sys; print(json.load(sys.stdin)['access'])")
BOB=$(curl -s -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "bob", "password": "pass1234"}' \
  | uv run python -c "import json, sys; print(json.load(sys.stdin)['access'])")

# 2人とも、商品 1 を1個カートに入れる
for T in "$ACCESS" "$BOB"; do
  curl -s -X POST http://127.0.0.1:8000/api/cart/items -H "Authorization: Bearer $T" \
    -H "Content-Type: application/json" -d '{"product_id": 1}'
done
```

同時に注文します。

```bash
curl -s -w " %{http_code}\n" -X POST http://127.0.0.1:8000/api/orders -H "Authorization: Bearer $ACCESS" &
curl -s -w " %{http_code}\n" -X POST http://127.0.0.1:8000/api/orders -H "Authorization: Bearer $BOB" &
wait
```

```text
{"id": ..., "total": "2980.00", "created_at": ..., "items": [{"product_id": 1, "price": "2980.00", "quantity": 1}]} 201
{"id": ..., "total": "2980.00", "created_at": ..., "items": [{"product_id": 1, "price": "2980.00", "quantity": 1}]} 201
```

✅ 検証済み: 在庫は `0`、Orders は**2件**。1個しか無いのに、2人とも買えた

> 💡補足: 行末の `&` は「終わるのを待たずに次へ進む」（シェルの機能）。`wait` は、`&` で走らせたものが全部終わるまで待つ。これで2本がほぼ同時に出る。

ログの SQL（2人ぶんを抜き出したもの）です。2人とも同じ `quantity = 0` を書いています。

```sql
UPDATE `shop_inventory` SET `product_id` = 1, `quantity` = 0 WHERE `shop_inventory`.`id` = 1;  -- alice
COMMIT;
UPDATE `shop_inventory` SET `product_id` = 1, `quantity` = 0 WHERE `shop_inventory`.`id` = 1;  -- bob
COMMIT;
```

✅ 検証済み: MySQL 8.4.11（開発サーバの SQL ログ）

**② 在庫を直す**（`shop/api.py`。`time.sleep` はまだ残す）

import を2か所直す

```diff
 from django.db import transaction
+from django.db.models import F
 from django.http import HttpRequest
```

```diff
-from .models import Cart, CartItem, Order, OrderItem, Product
+from .models import Cart, CartItem, Inventory, Order, OrderItem, Product
```

`place_order` の中を2か所直す。まず、カートを読む行（在庫はもう読まない）

```diff
-    cart_items = list(cart.items.select_related("product__inventory"))
+    cart_items = list(cart.items.select_related("product"))
```

次に、`for ci in cart_items:` から `inventory.save()` までの7行を、まるごと置き換える

```python
        for ci in cart_items:
            # 在庫が足りているときだけ減らす。比べるのも引くのも、MySQL が UPDATE 1本の中でやる
            updated = Inventory.objects.filter(
                product=ci.product, quantity__gte=ci.quantity
            ).update(quantity=F("quantity") - ci.quantity)
            if updated == 0:
                # 例外で with を抜けると、上で作った注文と明細も無かったことになる
                raise HttpError(409, f"「{ci.product.name}」の在庫が足りません")
```

✅ 検証済み: django-ninja 1.7.1（ruff・mypy も通過）

> 💡補足: `quantity__gte` は 2-11 のフィールドルックアップ。`gte` は「以上」（greater than or equal）で、SQL では `>=` になる。

在庫を `1` に戻し、①のカート投入と同時注文を、もう一度やります。

```text
{"id": ..., "total": "2980.00", "created_at": ..., "items": [...]} 201
{"detail": "「Django 入門」の在庫が足りません"} 409
```

```sql
UPDATE `shop_inventory` SET `quantity` = (`shop_inventory`.`quantity` - 1)
  WHERE (`shop_inventory`.`product_id` = 1 AND `shop_inventory`.`quantity` >= 1);  -- alice: 1行
COMMIT;
UPDATE `shop_inventory` SET `quantity` = (`shop_inventory`.`quantity` - 1)
  WHERE (`shop_inventory`.`product_id` = 1 AND `shop_inventory`.`quantity` >= 1);  -- bob: 0行
ROLLBACK;
```

✅ 検証済み: MySQL 8.4.11（在庫は `0`、Orders は1件。bob のカートは残る）

確かめたら、①で足した `import time` と `time.sleep(1)` の2行を**消します**。

**③ カートの足し算も直す**（`shop/api.py` の `add_to_cart`）

`if not created:` の中の3行を置き換える

```python
    if not created:
        # もう入っていたら、行は増やさずに数を足す。足し算は MySQL にさせる
        CartItem.objects.filter(id=item.id).update(quantity=F("quantity") + payload.quantity)
        item = CartItem.objects.get(id=item.id)  # 足したあとの数を読み直す
```

✅ 検証済み: Django 5.2.17（3-2 のテストは何も変えずに通る）

`update()` は MySQL に書くだけで、手元の `item` の数は古いままです。返す前に、もう一度読み直します。

**④ テスト**（`tests/test_orders.py` の最後に追加）

要件だけ書きます。

1. 在庫を1にして、alice と bob の2人が商品をカートに入れる
2. alice が注文すると 201、続けて bob が注文すると 409
3. 在庫は `0` のまま（マイナスにならない）

<details><summary>解答例</summary>

```python
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
```

</details>

✅ 検証済み: pytest-django 4.14.0（`47 passed`。ruff・mypy も通過）

> ⏭️ **後で回収**: このテストは2人を**順番に**通すので、直す前のコードでも通る。本当に同時に走らせるテストは、第3部-8（トランザクションのテスト）で書く。

### 4-2. 🔬 仕組み解剖

| | `F()` 式 | `QuerySet.update()` |
| --- | --- | --- |
| 正式名称 | django.db.models.F（F expression） | QuerySet.update() |
| いつ・誰が | Django は値を計算しない。SQL の中に `quantity - 1` と書くだけ。計算は、SQL を実行する瞬間に MySQL がする | 呼んだときに Django が `UPDATE ... WHERE ...` を1本送る。戻り値は、書き換えた行の数 |
| 発行される SQL | `SET quantity = (quantity - 1)` | `UPDATE shop_inventory SET ... WHERE product_id = 1 AND quantity >= 1` |
| TS での対応物 | 対応物なし（ORM の機能）。Prisma の `{ decrement: 1 }` が同じ役目 | 対応物なし（ORM の機能）。Prisma の `updateMany` が同じ役目 |
| なぜこの設計 | Python で計算すると、「読んだ時点の値」で書いてしまう。MySQL に計算させれば、書く瞬間の値が使われる | 行を読まずに済む。条件（`quantity >= 1`）と書き換えを1本にまとめられる |
| 失敗すると | 条件を付けずに `F("quantity") - 1` だけにすると、在庫0のとき3-1の `CHECK` に当たる。`IntegrityError (3819)` で 500（確認済み） | 行ごとの `save()` を通らない。`auto_now` の項目も更新されない。条件に合う行が無ければ `0` が返るだけで、例外にはならない |

✅ 検証済み: Django 5.2.17 / MySQL 8.4.11

**直す前**（①）

```text
  A (alice)                       B (bob)                         stock
  ------------------------------  ------------------------------  -----
  SELECT ... reads 1                                              1
                                  SELECT ... reads 1              1
  1 >= 1 ok                       1 >= 1 ok                       1
  UPDATE SET quantity = 0                                         0
  COMMIT -> 201                                                   0
                                  UPDATE SET quantity = 0         0
                                  COMMIT -> 201                   0
```

**直したあと**（②）

```text
  A (alice)                       B (bob)                         stock
  ------------------------------  ------------------------------  -----
  UPDATE ... WHERE quantity >= 1  UPDATE ... WHERE quantity >= 1  1
    -> 1 row changed                -> waits until A finishes     0
  COMMIT -> 201                                                   0
                                    -> sees 0: 0 rows changed     0
                                  ROLLBACK -> 409                 0
```

✅ 検証済み: ①②の SQL ログ

見てほしいのは、直す前は2人とも**自分が読んだ `1`** で判断している点です。直したあとは、判断（`>= 1`）が UPDATE の中に入ったので、bob は alice が書いた後の `0` で判断します。

> ⏭️ **後で回収**: bob の UPDATE が「alice が終わるまで待つ」のは、MySQL が書き換え中の行に鍵をかけるから（行ロック）。第3部-5 で、この鍵を自分からかける `select_for_update()` と一緒に扱う。

### 4-3. 🐍 Python注

新しい文法はありません。

### 4-4. 解説 — なぜこう設計するか

3-3 の `transaction.atomic` は「途中で失敗したら取り消す」仕組みです。「他の人が同じ行を同時に読む」ことは止めません。2人とも失敗していないので、2人とも確定しました。

🧠 Django の考え方: 「読んで、計算して、書く」を Python でやらない。計算と条件を SQL 1本に入れて、DB にやらせる。

これで、3-2 と 3-3 の ⏭️ を回収しました。

### 4-5. 🏢 実務メモ

> 🏢 **実務メモ**: 公式ドキュメントは、`F()` の利点として「2つのスレッドが同じ値を書き換えるときの競合（race condition）を避けられる」ことを挙げている。在庫・残高・いいね数など、数を足し引きする項目は `F()` で書く。
> 根拠: https://docs.djangoproject.com/en/5.2/ref/models/expressions/#avoiding-race-conditions-using-f

### 4-6. 🔮 予測 → 動作確認

1. shell で、同じカートの行を `a`・`b` の2つの変数に読み込む（数は1）。`a.quantity += 1; a.save()`、続けて `b.quantity += 1; b.save()` すると、台帳の数は？
2. 在庫の行（Inventory）が無い商品を注文すると？ 3-1 では、在庫の行が無いと一覧が 500 だった
3. ②の `quantity__gte=ci.quantity` の条件を消して、在庫0の商品を注文すると？

<details><summary>答え</summary>

1. `3` ではなく `2`。b は「自分が読んだ1」に1を足して、`quantity = 2` を書く。a の足し算が消える（検証済み）
2. 409（在庫が足りません）。在庫の行が無いので、`update()` が書き換えた行は `0`。直す前は、`ci.product.inventory` で例外になり 500 だった（検証済み）
3. 500。MySQL が `-1` にしようとして、3-1 の `CHECK`（0以上）に当たる。`IntegrityError (3819)`（検証済み）

</details>

### 4-7. ✅ 想起チェック

1. `F("quantity") - 1` の引き算は、Python と MySQL のどちらがする？
2. `update()` の戻り値は何？ この回では、それを何に使った？

<details><summary>答え</summary>

1. MySQL。SQL を実行する瞬間の値で引く
2. 書き換えた行の数。`0` なら「在庫が足りなかった」とみなして 409 にした

</details>

### 4-8. 📇 まとめカード

この回で覚えることは1つだけ: **数を足し引きするときは `F()` で MySQL に計算させる。条件も同じ `UPDATE` に入れる。**

📒 用語集に追記: `F()` 式 / `QuerySet.update()` / 競合（レースコンディション）

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第3部 ステップ5` — 行ロックで守る


---

## 第3部-5: 行ロックで守る

**❓ この回の問い**: 3-4 で、在庫の「比べて引く」を UPDATE 1本に入れて、最後の1個が2人に売れなくなった。では、**同じ人が注文ボタンを2回押したら**？ カートの中身は1回ぶんしか無い

**作るもの**: 同じカートが2回注文されるのを起こし、`select_for_update()` でカートの行に鍵をかけて直す
**重要度**: 🟡 読めればよい — 書く場面は限られる。ただ、お金や在庫を扱うコードでは必ず出会う
**前ステップとの接続**: 3-4 の `place_order` の「カートを読む」部分を、`atomic` の中に入れて鍵をかける

### 5-0. このステップの初出

**Django / Ninja**: `select_for_update()`, 分離レベル / **Python**: なし

> 🧒 **かみくだくと**: **行ロック**（row lock）は、台帳の1行に「今わたしが使っています」の札を掛けること。札の掛かった行を、他の人は書き換えられないし、札を掛けることもできない。持ち主のトランザクションが終わる（コミットかロールバック）まで待たされる。

> 🧒 **かみくだくと**: **select_for_update()** は、読むと同時にその行へ札を掛ける命令。SQL の最後に `FOR UPDATE` が付く。

> 🧒 **かみくだくと**: **分離レベル**（isolation level）は、「他の人が確定した書き込みが、自分のトランザクションの中で、いつ見えるか」の決まり。

### 5-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

**① 壊れるのを見る**

3-4 の①と同じく、`shop/api.py` に**一時的に** `import time` と `time.sleep(1)` を足します（`raise HttpError(400, "カートが空です")` の下）。

管理画面で商品 1 の在庫を `5` にし、alice のカートに商品 1 を1個入れます（`ACCESS` は 3-4 と同じ取り方）。

```bash
curl -s -X POST http://127.0.0.1:8000/api/cart/items -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" -d '{"product_id": 1}'
```

同じ身分証で、2回同時に注文します（ボタンの2度押し）。

```bash
curl -s -w " %{http_code}\n" -X POST http://127.0.0.1:8000/api/orders -H "Authorization: Bearer $ACCESS" &
curl -s -w " %{http_code}\n" -X POST http://127.0.0.1:8000/api/orders -H "Authorization: Bearer $ACCESS" &
wait
```

```text
{"id": ..., "total": "2980.00", "created_at": ..., "items": [{"product_id": 1, "price": "2980.00", "quantity": 1}]} 201
{"id": ..., "total": "2980.00", "created_at": ..., "items": [{"product_id": 1, "price": "2980.00", "quantity": 1}]} 201
```

✅ 検証済み: 注文が**2件**でき、在庫は `5` → `3`。カートには1個しか無かったのに、2回ぶん売れた

在庫は十分あるので、3-4 の `WHERE quantity >= 1` は2回とも通ります。壊れたのは在庫ではなく、**カートを2回読んだこと**です。`F()` では直せません。

**② カートに鍵をかける**（`shop/api.py`）

`place_order` を、関数**まるごと**置き換える（カートを読む行が `with` の中に入るので、字下げが変わる）

```python
@order_router.post("", response={201: OrderOut}, auth=JWTAuth())
def place_order(request: HttpRequest):
    assert request.user.is_authenticated
    # ここから下は「全部やるか、何もしないか」。途中で例外が出たら、全部取り消す
    with transaction.atomic():
        # カートの行に鍵をかけて読む。同じカートの2つ目の注文は、1つ目が終わるまでここで待つ
        cart = get_object_or_404(Cart.objects.select_for_update(), user=request.user)
        cart_items = list(cart.items.select_related("product"))
        if not cart_items:
            raise HttpError(400, "カートが空です")

        total = sum((ci.product.price * ci.quantity for ci in cart_items), Decimal("0"))
        order = Order.objects.create(user=request.user, total=total)
        # 注文の明細を、INSERT 1本でまとめて作る
        OrderItem.objects.bulk_create(
            [
                OrderItem(
                    order=order, product=ci.product, price=ci.product.price, quantity=ci.quantity
                )
                for ci in cart_items
            ]
        )
        for ci in cart_items:
            # 在庫が足りているときだけ減らす。比べるのも引くのも、MySQL が UPDATE 1本の中でやる
            updated = Inventory.objects.filter(
                product=ci.product, quantity__gte=ci.quantity
            ).update(quantity=F("quantity") - ci.quantity)
            if updated == 0:
                # 例外で with を抜けると、上で作った注文と明細も無かったことになる
                raise HttpError(409, f"「{ci.product.name}」の在庫が足りません")

        cart.items.all().delete()  # カートを空にする

    return Status(201, order)
```

✅ 検証済み: django-ninja 1.7.1（ruff・mypy も通過）

> 💡補足: `get_object_or_404` には、モデルの代わりに `Cart.objects.select_for_update()` のような QuerySet も渡せる。探し方の指定ごと渡せる。

もう一度確かめるため、`time.sleep(1)` を `raise HttpError(400, "カートが空です")` の下に入れ直します（今度は `with` の中なので、字下げは8つ）。在庫を `5` に戻し、カートに1個入れて、①の2度押しをもう一度。

```text
{"id": ..., "total": "2980.00", "created_at": ..., "items": [{"product_id": 1, "price": "2980.00", "quantity": 1}]} 201
{"detail": "カートが空です"} 400
```

```sql
BEGIN;  -- 1回目
SELECT ... FROM `shop_cart` WHERE `shop_cart`.`user_id` = 1 LIMIT 21 FOR UPDATE;  -- 0.000秒
BEGIN;  -- 2回目
...（1回目: 注文・明細・在庫・カートを空に）
COMMIT;  -- 1回目。ここで札が外れる
SELECT ... FROM `shop_cart` WHERE `shop_cart`.`user_id` = 1 LIMIT 21 FOR UPDATE;  -- 2回目: 1.021秒（待っていた）
SELECT ... FROM `shop_cartitem` ...;  -- 2回目: もう空
ROLLBACK;  -- 2回目
```

✅ 検証済み: MySQL 8.4.11（開発サーバの SQL ログ。行頭の `(1.021)` が待った時間）

確かめたら、`import time` と `time.sleep(1)` を**消します**。

**③ 分離レベルを見る**

```bash
uv run python manage.py shell -c "
from django.db import connection
with connection.cursor() as c:
    c.execute('SELECT @@transaction_isolation, @@global.transaction_isolation')
    print(c.fetchone())
"
```

```text
('READ-COMMITTED', 'REPEATABLE-READ')
```

✅ 検証済み: Django 5.2.17 / MySQL 8.4.11

MySQL の既定は `REPEATABLE-READ`（右）ですが、Django は接続するたびに `READ-COMMITTED`（左）に変えています。SQL ログの先頭に出る `SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED` がそれです。

**④ テスト**（`tests/test_orders.py` の最後に追加）

要件だけ書きます。

1. カートに1個入れて注文すると 201
2. もう一度注文すると 400。注文は1件のまま、在庫は1個だけ減っている

<details><summary>解答例</summary>

```python
def test_second_click_finds_empty_cart(
    user: User, book: Product, auth_headers: dict[str, str]
) -> None:
    put_in_cart(user, book, 1)

    assert client.post("/orders", headers=auth_headers).status_code == 201
    res = client.post("/orders", headers=auth_headers)  # もう一度押した

    assert res.status_code == 400  # カートはもう空
    assert Order.objects.count() == 1
    assert Inventory.objects.get(product=book).quantity == 4  # 1個だけ減る
```

</details>

✅ 検証済み: pytest-django 4.14.0（`48 passed`。ruff・mypy も通過）

3-4 と同じく、このテストは順番に押すので、鍵が無くても通ります。同時に押すテストは、3-4 で予告したとおり第3部-8 で書きます。

### 5-2. 🔬 仕組み解剖

| | `select_for_update()` | 分離レベル |
| --- | --- | --- |
| 正式名称 | QuerySet.select_for_update() | transaction isolation level（Django の設定は `OPTIONS` の `isolation_level`） |
| いつ・誰が | 評価したときに Django が `SELECT ... FOR UPDATE` を送る。MySQL が行に札を掛け、`COMMIT` / `ROLLBACK` で外す | Django が接続するたびに `SET SESSION TRANSACTION ISOLATION LEVEL ...` を送る。以降の SELECT が何を見るかを MySQL が決める |
| 発行される SQL | `SELECT ... WHERE user_id = 1 LIMIT 21 FOR UPDATE` | `SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED` |
| TS での対応物 | 対応物なし（DB の機能）。Prisma には専用の書き方が無く、生 SQL で `FOR UPDATE` を書く | 対応物なし（DB の機能）。Prisma の `$transaction` の `isolationLevel` が同じ設定 |
| なぜこの設計 | 「読んで、Python で判断して、書く」の間、他の人に同じ行を触らせない。`F()` で SQL 1本にできない処理を守る | 同時の読み書きをどこまで隔てるかは、速さとのかね合い。Django は MySQL では `READ COMMITTED` を既定にしている |
| 失敗すると | `atomic` の外で使うと `TransactionManagementError: select_for_update cannot be used outside of a transaction.`（確認済み）。札は1つ目の SQL ですぐ外れてしまうので、Django が止める | `REPEATABLE READ` にすると、下の表のように「古い値」を読み続けることがある |

✅ 検証済み: Django 5.2.17 / MySQL 8.4.11

**直す前**（①）と**直したあと**（②）

```text
  click 1                           click 2
  --------------------------------  --------------------------------
  read cart: 1 item                 read cart: 1 item
  BEGIN, order 1, stock -1          BEGIN, order 2, stock -1
  COMMIT -> 201                     COMMIT -> 201
```

```text
  click 1                           click 2
  --------------------------------  --------------------------------
  BEGIN                             BEGIN
  lock cart (FOR UPDATE)            lock cart -> waits ...
  read cart: 1 item                      :
  order 1, stock -1, empty cart          :
  COMMIT -> 201 (lock released)          :
                                    lock cart -> got it
                                    read cart: 0 items
                                    ROLLBACK -> 400
```

✅ 検証済み: ①②の SQL ログ

見てほしいのは、2回目が「カートを読む」**前**で止まっている点です。札が外れてから読むので、1回目が空にしたあとのカートを見ます。

**分離レベルで、読める値が変わる**

トランザクションの中で在庫を読み（`5`）、そのあと別の人が `2` に書き換えて確定しました。同じトランザクションの中で、もう一度読むと次のようになります。

| 分離レベル | 1回目の SELECT | 2回目の SELECT | `SELECT ... FOR UPDATE` |
| --- | --- | --- | --- |
| `READ COMMITTED`（Django の既定） | 5 | **2**（確定した最新） | 2 |
| `REPEATABLE READ`（MySQL の既定） | 5 | **5**（1回目と同じ） | 2 |

✅ 検証済み: MySQL 8.4.11（2本の接続で確認）

`FOR UPDATE` は、分離レベルに関係なく最新の値を読みます。3-4 の UPDATE も同じで、書き換える行は必ず最新の値で判断します。

> ⏭️ **3-4 の回収**: 3-4 で bob の UPDATE が「alice が終わるまで待った」のは、alice の UPDATE がその行に札を掛けていたから。UPDATE は、書き換える行に自動で札を掛ける。

### 5-3. 🐍 Python注

新しい文法はありません。

### 5-4. 解説 — なぜこう設計するか

鍵を掛けたのは、在庫ではなく**カート**の行です。守りたいのは「同じカートを2回注文しない」ことだからです。別の人のカートは別の行なので、alice と bob が同時に注文しても、お互いを待ちません（2人同時で、どちらも約1秒で 201 を確認済み）。

🧠 Django の考え方: SQL 1本で済むなら `F()`。Python で判断が要るなら、`atomic` の中で `select_for_update()` してから読む。

### 5-5. 🏢 実務メモ

> 🏢 **実務メモ**: 札を掛けている間、他の人は待たされる。MySQL の公式ドキュメントは、トランザクションを小さく短く保つよう勧めている。`atomic` の中で、外部 API の呼び出しやメール送信のような遅い処理をしない。
> 根拠: https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlocks-handling.html

### 5-6. 🔮 予測 → 動作確認

1. `with transaction.atomic():` の外で `Cart.objects.select_for_update().get(...)` を呼ぶと？
2. ②のあと、alice と bob が同時に注文したら、bob は alice の終わりを待つ？
3. `config/settings.py` の `OPTIONS` に `"isolation_level": "repeatable read"` を足したら、SQL ログの先頭の `SET SESSION ...` はどう変わる？

<details><summary>答え</summary>

1. `TransactionManagementError: select_for_update cannot be used outside of a transaction.`（検証済み）。鍵がすぐ外れて意味が無いので、Django が止める
2. 待たない。札はカートの行ごとで、alice と bob のカートは別の行（検証済み）
3. `SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ` に変わる。ただし公式ドキュメントは、MySQL では `repeatable read` だとデータが失われることがあると注意している。試したら元に戻す
   根拠: https://docs.djangoproject.com/en/5.2/ref/databases/#mysql-isolation-level

</details>

### 5-7. ✅ 想起チェック

1. `select_for_update()` で掛けた札は、いつ外れる？
2. 「在庫を引く」は `F()` で守った。「同じカートを2回注文しない」は、なぜ `F()` では守れない？

<details><summary>答え</summary>

1. その `atomic` が終わるとき（`COMMIT` か `ROLLBACK`）
2. 壊れたのは「カートを読んで、注文を作る」の部分で、SQL 1本の足し引きにできないから。読む前に札を掛けて、他の注文を待たせる

</details>

### 5-8. 📇 まとめカード

この回で覚えることは1つだけ: **読んでから Python で判断するなら、`atomic` の中で `select_for_update()` して、その行に札を掛けてから読む。**

📒 用語集に追記: 行ロック / `select_for_update()` / 分離レベル（`READ COMMITTED` / `REPEATABLE READ`）

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第3部 ステップ6` — 注文ステータス


---

## 第3部-6: 注文ステータス

**❓ この回の問い**: 3-5 までで、注文は壊れずに確定できるようになった。確定した注文は、このあと発送され、届いて完了する。では、その「状態」をどこに持ち、「確定からいきなり完了」のような飛ばしを、どこで断る？

**作るもの**: 注文に状態（確定 → 発送済み → 完了）を持たせ、`PATCH /api/orders/{id}/status` でお店の人が1段ずつ進める
**重要度**: 🔴 毎日使う — 「決まった値の中から1つ」の項目と、そのルールを持つメソッドは、どのアプリにも出てくる
**前ステップとの接続**: 3-3 の Order に `status` を足す。2-14 の `soft_delete()` と同じく、ルールをモデルのメソッドに書く

### 6-0. このステップの初出

**Django / Ninja**: `TextChoices`, モデルメソッド（業務ルールを置く場所として） / **Python**: クラスの中のクラス

> 🧒 **かみくだくと**: **TextChoices** は、「この項目に入れてよい文字列の一覧表」。台帳に入る値（`"shipped"`）と、人が読む名前（`発送済み`）を組にして並べる。

> 🧒 **かみくだくと**: **モデルメソッド**は、モデルのクラスに書く関数。2-14 の `soft_delete()` がそう。この回は「状態はこの順にしか進めない」という**お店の決まり**（業務ルール）を、API ではなくモデルに書く。

> 🧒 **かみくだくと**: **is_staff** は、ユーザーの「お店の人か」の印（`True` / `False`）。1-4 の `createsuperuser` で作った `admin` は `True`。管理画面に入れるかどうかも、この印で決まる。

### 6-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

**① モデル**（`shop/models.py` の `class Order` を、まるごと置き換え）

```python
class Order(models.Model):
    class Status(models.TextChoices):
        # 名前 = "台帳に入る値", "人が読む名前"
        PLACED = "placed", "確定"
        SHIPPED = "shipped", "発送済み"
        COMPLETED = "completed", "完了"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    total = models.DecimalField(max_digits=12, decimal_places=2)  # 合計金額（確定した時点）
    # 注文の状態。選べる値は Status の3つ。作ったときは「確定」
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLACED)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"注文 {self.id}"

    def change_status(self, new_status: str) -> None:
        # 進んでよいのは「確定 → 発送済み → 完了」の順だけ（今の状態: 次に進める状態）
        next_status: dict[str, str] = {
            Order.Status.PLACED: Order.Status.SHIPPED,
            Order.Status.SHIPPED: Order.Status.COMPLETED,
        }
        if next_status.get(self.status) != new_status:
            new_label = Order.Status(new_status).label
            raise ValueError(f"「{self.get_status_display()}」から「{new_label}」には進めません")
        self.status = new_status
        self.save(update_fields=["status"])
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17（ruff・mypy も通過）

```bash
uv run python manage.py makemigrations shop
uv run python manage.py sqlmigrate shop 0004
uv run python manage.py migrate
```

```sql
ALTER TABLE `shop_order` ADD COLUMN `status` varchar(20) DEFAULT 'placed' NOT NULL;
ALTER TABLE `shop_order` ALTER COLUMN `status` DROP DEFAULT;
```

✅ 検証済み: `shop/migrations/0004_order_status.py` ができる。今ある注文は、全部 `placed` で埋まる

**② API**（`shop/api.py`）

`OrderOut` に1行足す（`total` の下）

```python
    status: Order.Status  # "placed" / "shipped" / "completed" のどれか
```

ファイルの**最後**に追加

```python
class OrderStatusIn(Schema):
    status: Order.Status  # 3つ以外の値は 422


@order_router.patch("/{order_id}/status", response=OrderOut, auth=JWTAuth())
def change_order_status(request: HttpRequest, order_id: int, payload: OrderStatusIn):
    # 状態を進めるのはお店の人だけ（管理画面に入れるスタッフ）
    if not request.user.is_staff:
        raise HttpError(403, "お店の人しか変えられません")
    order = get_object_or_404(Order, id=order_id)
    try:
        order.change_status(payload.status)  # 進んでよいかは、モデルが決める
    except ValueError as e:
        raise HttpError(409, str(e)) from e
    return order
```

✅ 検証済み: django-ninja 1.7.1（ruff・mypy も通過）

> 💡補足: `shop/api.py` には、Ninja の `Status`（`Status(201, ...)` の）も import してある。注文の状態は `Order.Status` と、クラスの中に置いたので、名前がぶつからない。

**③ 試す**（`STAFF` は `admin` の身分証。取り方は 3-4 の `ACCESS` と同じで、パスワードは 1-4 で決めたもの。`<id>` は自分の注文の id）

```bash
curl -s -w " %{http_code}\n" -X PATCH http://127.0.0.1:8000/api/orders/<id>/status \
  -H "Authorization: Bearer $STAFF" -H "Content-Type: application/json" -d '{"status": "completed"}'
curl -s -w " %{http_code}\n" -X PATCH http://127.0.0.1:8000/api/orders/<id>/status \
  -H "Authorization: Bearer $STAFF" -H "Content-Type: application/json" -d '{"status": "shipped"}'
```

```text
{"detail": "「確定」から「完了」には進めません"} 409
{"id": ..., "total": "2980.00", "status": "shipped", "created_at": ..., "items": [...]} 200
```

✅ 検証済み: Django 5.2.17 / django-ninja 1.7.1

`{"status": "flying"}` なら 422（`Input should be 'placed', 'shipped' or 'completed'`）、`$ACCESS`（alice）なら 403 です（検証済み）。

**④ テスト**（`tests/test_order_status.py` 新規）

要件だけ書きます。

1. モデルだけを試す: 確定の注文で `change_status(Order.Status.COMPLETED)` すると `ValueError`。台帳は `placed` のまま
2. お店の人が `shipped` にすると 200 で、応答の `status` は `"shipped"`
3. 発送済みの注文を `placed` に戻そうとすると 409
4. お客（`auth_headers`）が変えようとすると 403

お店の人は、`create_user(..., is_staff=True)` で作れます。

<details><summary>解答例</summary>

```python
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
```

</details>

✅ 検証済み: pytest-django 4.14.0（`52 passed`。ruff・mypy も通過）

> 💡補足: `with pytest.raises(ValueError):` は、「この中で `ValueError` が出れば合格、出なければ不合格」という pytest の書き方。

### 6-2. 🔬 仕組み解剖

| | `TextChoices` | モデルメソッド（`change_status`） |
| --- | --- | --- |
| 正式名称 | 列挙型（enumeration types）の `TextChoices` と、フィールドの `choices` | model methods |
| いつ・誰が | 起動時に Python がクラスを作る。`choices` は、台帳には何も足さない（①の SQL は `varchar(20)` だけ）。値を確かめるのは Ninja のスキーマ（422）と、Django のモデル検証（`full_clean()`）と管理画面 | 呼んだときに Python が実行する。`save(update_fields=["status"])` で `UPDATE ... SET status = ...` を1本送る |
| 発行される SQL | `ADD COLUMN status varchar(20)`。`CHECK` は作られない | `UPDATE shop_order SET status = 'shipped' WHERE id = 1` |
| TS での対応物 | TS の `enum` や `"placed" \| "shipped" \| "completed"` が近い。ただしこちらは「人が読む名前」も一緒に持つ | クラスのメソッド。対応物そのもの |
| なぜこの設計 | 値（`"shipped"`）と名前（`発送済み`）を1か所で管理する。`get_status_display()`（Django が自動で作る）で名前が取れる | ルールをモデルに置けば、API・管理コマンド・テストのどこから呼んでも、同じ決まりが守られる |
| 失敗すると | `Order.objects.create(status="flying")` は**保存できてしまう**（DB に決まりが無い。確認済み）。`full_clean()` なら `Value 'flying' is not a valid choice.` | メソッドを通らずに `order.status = ...; order.save()` と書けば、ルールは守られない。管理画面も通らない（🔮の3） |

✅ 検証済み: Django 5.2.17 / MySQL 8.4.11

```text
  +--------+      +---------+      +-----------+
  | placed | ---> | shipped | ---> | completed |
  +--------+      +---------+      +-----------+
       |                                 ^
       +--------- x skip -> 409 ---------+
```

✅ 検証済み: ③と④（戻る向きも 409）

見てほしいのは、矢印が**右向きに1段ずつ**しか無い点です。`next_status` の辞書が、この矢印をそのまま書いたものです。

### 6-3. 🐍 Python注

> 🐍 **Python注**: `class Order:` の中の `class Status(...)` は、クラスの中に置いたクラス。外からは `Order.Status.SHIPPED` と呼ぶ。TS の `namespace` の中に `enum` を置くのに近い。

> 🐍 **Python注**: `next_status.get(key)` は、辞書に `key` が無ければ `None` を返す（例外にならない）。`completed` には次が無いので、何を渡しても進めない。

### 6-4. 解説 — なぜこう設計するか

「確定から完了に飛ばない」は、HTTP とは関係の無い**お店の決まり**です。API の関数に書くと、管理コマンドやバッチから状態を変えるとき、同じ `if` をもう一度書くことになります。モデルに置けば、だれが呼んでも1か所で守られます。API の関数は、決まりの**結果**（`ValueError`）を 409 に訳すだけです。

🧠 Django の考え方: 業務ルールはモデルのメソッドに置く。ビュー（API の関数）は、HTTP の出入りに専念する。

### 6-5. 🏢 実務メモ

> 🏢 **実務メモ**: Django の公式ドキュメントは、モデルメソッドを「業務ロジックを1か所（モデル）にまとめる、価値のあるやり方」と紹介している。
> 根拠: https://docs.djangoproject.com/en/5.2/topics/db/models/#model-methods

### 6-6. 🔮 予測 → 動作確認

1. `migrate` のあと、3-3〜3-5 で作った注文の `status` は何になっている？
2. shell で `Order.objects.create(user=..., total=1, status="flying")` すると？
3. 管理画面で、確定の注文の Status を「完了」に変えて保存すると？

<details><summary>答え</summary>

1. 全部 `placed`。①の SQL の `DEFAULT 'placed'` で埋まり、そのあと既定値は外される（検証済み）
2. 保存できる。`choices` は DB に決まりを作らないから。`get_status_display()` も `flying` をそのまま返す（検証済み）
3. 保存できる。管理画面は「3つのどれか」までは確かめるが、`change_status()` は通らない（検証済み）。管理画面はデータを見る窓で、業務の操作口にはしない

</details>

### 6-7. ✅ 想起チェック

1. `TextChoices` の1行 `SHIPPED = "shipped", "発送済み"` で、台帳に入るのはどっち？
2. 「確定から完了に飛べない」というルールは、API の関数ではなくどこに書いた？ それはなぜ？

<details><summary>答え</summary>

1. `"shipped"`。`発送済み` は人が読む名前で、`get_status_display()` や管理画面で使われる
2. モデルのメソッド（`change_status`）。どこから呼んでも同じルールが守られるから

</details>

### 6-8. 📇 まとめカード

この回で覚えることは1つだけ: **決まった値は `TextChoices`、その値の変え方のルールはモデルのメソッドに書く。**

📒 用語集に追記: `TextChoices` / `choices` / モデルメソッド / `is_staff`

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第3部 ステップ7` — レビューと集計


---

## 第3部-7: レビューと集計

**❓ この回の問い**: 3-6 で、注文の流れができた。買った人は感想を残したい。商品一覧に「★4.5（2件）」を出すには、商品ごとにレビューを数える必要がある。商品が100個あったら、SQL は何本？

**作るもの**: レビュー（星1〜5 と感想）を書く API。商品の一覧と詳細に、レビューの件数と星の平均を付ける
**重要度**: 🔴 毎日使う — 「〜ごとの件数・合計・平均」は、一覧画面のたびに出てくる
**前ステップとの接続**: 3-1 の商品 API の応答に、2つの項目を足す。2-4 の N+1 の考え方を「数える」に広げる

### 7-0. このステップの初出

**Django / Ninja**: `annotate()`, `Count` / `Avg`（集計関数） / **Python**: なし

> 🧒 **かみくだくと**: **集計関数**（aggregate functions）は、何行かをまとめて1つの値にする計算。`Count` は件数、`Avg` は平均。SQL の `COUNT()`・`AVG()` になる。

> 🧒 **かみくだくと**: **annotate()** は、取ってくる行の1つ1つに、計算した値を**付け足す**命令。「商品ごとの件数」のように、行ごとにまとめた値を付けられる。

### 7-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

**① モデル**（`shop/models.py` の**最後**に追加）

```python
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField()  # 星の数（1〜5）
    comment = models.TextField(blank=True)  # 感想。空でもよい
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # 1人1商品に1件まで
            models.UniqueConstraint(
                fields=["product", "user"], name="shop_review_unique_product_user"
            ),
            # 星は1〜5
            models.CheckConstraint(
                condition=Q(rating__gte=1, rating__lte=5), name="shop_review_rating_1_to_5"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product.name} ★{self.rating}"
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17（ruff・mypy も通過）

`shop/admin.py` は、import を `Review` 入りに置き換え（1行に収まらないので、ruff が縦に並べる形）、最後に1行足す

```python
from .models import (
    Cart,
    CartItem,
    Inventory,
    Order,
    OrderItem,
    Product,
    ProductImage,
    Review,
)
```

```python
admin.site.register(Review)
```

```bash
uv run python manage.py makemigrations shop
uv run python manage.py migrate
```

✅ 検証済み: `shop/migrations/0005_review.py` ができる

一意制約（3-2）とチェック制約（3-1）は、もう知っている道具です。新しいのは②からです。

**② 件数と平均を付ける**（`shop/api.py`）

import を2か所直す

```diff
-from django.db.models import F
+from django.db.models import Avg, Count, F
```

```diff
-from .models import Cart, CartItem, Inventory, Order, OrderItem, Product
+from .models import Cart, CartItem, Inventory, Order, OrderItem, Product, Review
```

`ProductOut` の `stock` の行から、`get_product` の最後の行までを、まるごと置き換える

```python
    stock: int = Field(alias="inventory.quantity")  # 在庫の数（一対一の先をたどる）
    review_count: int  # レビューの件数（annotate で付け足した値）
    rating_avg: float | None  # 星の平均。レビューが無ければ null


def products_with_rating():
    # 在庫は JOIN で取り、レビューの件数と星の平均は MySQL に数えさせて、商品ごとに付け足す
    return Product.objects.select_related("inventory").annotate(
        review_count=Count("reviews"), rating_avg=Avg("reviews__rating")
    )


@router.get("", response=list[ProductOut])
def list_products(request: HttpRequest):
    return products_with_rating().order_by("id")


@router.get("/{product_id}", response=ProductOut)
def get_product(request: HttpRequest, product_id: int):
    return get_object_or_404(products_with_rating(), id=product_id)
```

✅ 検証済み: django-ninja 1.7.1（ruff・mypy も通過）

一覧と詳細の両方が同じ `ProductOut` を返すので、件数と平均の付け方を `products_with_rating()` の1か所にまとめました。片方だけ `annotate` を忘れると、`review_count` が無くて 500 になります。

**③ レビューを書く API**（`get_product` のすぐ下に追加）

```python
class ReviewIn(Schema):
    rating: int = Field(ge=1, le=5)  # 星は1〜5。外れたら 422
    comment: str = ""


class ReviewOut(Schema):
    id: int
    product_id: int
    user_id: int
    rating: int
    comment: str


@router.post("/{product_id}/reviews", response={201: ReviewOut}, auth=JWTAuth())
def create_review(request: HttpRequest, product_id: int, payload: ReviewIn):
    product = get_object_or_404(Product, id=product_id)
    assert request.user.is_authenticated
    if Review.objects.filter(product=product, user=request.user).exists():
        raise HttpError(409, "この商品には、もうレビューを書いています")
    review = Review.objects.create(
        product=product, user=request.user, rating=payload.rating, comment=payload.comment
    )
    return Status(201, review)
```

✅ 検証済み: django-ninja 1.7.1（ruff・mypy も通過）

`exists()` で 409 を返し、DB の一意制約を「最後の砦」にする形は、2-8 の会員登録と同じです。

**④ 試す**（`ACCESS` は alice、`BOB` は bob。取り方は 3-4 と同じ）

```bash
curl -s -X POST http://127.0.0.1:8000/api/products/1/reviews -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" -d '{"rating": 5, "comment": "分かりやすい"}'
curl -s -X POST http://127.0.0.1:8000/api/products/1/reviews -H "Authorization: Bearer $BOB" \
  -H "Content-Type: application/json" -d '{"rating": 4}'
curl -s http://127.0.0.1:8000/api/products
```

```text
[{"id": 1, "name": "Django 入門", "price": "2980.00", "category_id": 1, "stock": ..., "review_count": 2, "rating_avg": 4.5}, {"id": 2, "name": "Python ノート", "price": "450.50", "category_id": 1, "stock": ..., "review_count": 0, "rating_avg": null}]
```

✅ 検証済み: Django 5.2.17 / MySQL 8.4.11

一覧の SQL は、商品がいくつあっても **1本**です。

```sql
SELECT `shop_product`.`id`, ..., COUNT(`shop_review`.`id`) AS `review_count`, AVG(`shop_review`.`rating`) AS `rating_avg`, `shop_inventory`.`id`, ...
FROM `shop_product`
LEFT OUTER JOIN `shop_review` ON (`shop_product`.`id` = `shop_review`.`product_id`)
LEFT OUTER JOIN `shop_inventory` ON (`shop_product`.`id` = `shop_inventory`.`product_id`)
GROUP BY `shop_product`.`id`, `shop_inventory`.`id`
ORDER BY `shop_product`.`id` ASC;
```

✅ 検証済み: MySQL 8.4.11（`CaptureQueriesContext` で取得。列の一部を `...` に省略）

**⑤ テスト**

`tests/test_products.py` の `test_list_products` は、応答をまるごと比べているので、2行足す（`"stock": 5,` の下）

```python
            "review_count": 0,  # レビューはまだ無い
            "rating_avg": None,
```

`tests/test_reviews.py` を新しく作る。要件だけ書きます。

1. 星4と星5のレビューがある商品を `GET /products/{id}` すると、`review_count` は `2`、`rating_avg` は `4.5`
2. 同じ人が同じ商品に2回書くと、2回目は 409。レビューは1件のまま
3. 星6は 422

商品の fixture には、在庫の行も作ってください（無いと 3-1 のとおり 500）。

<details><summary>解答例</summary>

```python
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
```

</details>

✅ 検証済み: pytest-django 4.14.0（`55 passed`。ruff・mypy も通過）

### 7-2. 🔬 仕組み解剖

| | `annotate()` | `Count` / `Avg` |
| --- | --- | --- |
| 正式名称 | QuerySet.annotate() | 集計関数（aggregation functions）。`django.db.models.Count` / `Avg` |
| いつ・誰が | 一覧を評価したときに、Django が `GROUP BY` 付きの SELECT を1本作る。付け足した値は、各行の属性（`product.review_count`）になる | 計算するのは MySQL。`"reviews__rating"` は 2-11 と同じ `__` で、関連の先の項目を指す |
| 発行される SQL | `... GROUP BY shop_product.id, shop_inventory.id` | `COUNT(shop_review.id)`・`AVG(shop_review.rating)` |
| TS での対応物 | 対応物なし（ORM の機能）。Prisma の `_count` / `groupBy` が近い | 対応物なし（DB の機能）。Prisma の `_avg` が同じ役目 |
| なぜこの設計 | 行を全部 Python に持ってきて数えると、転送も SQL の本数も増える。数えるのは DB の得意分野 | `LEFT OUTER JOIN` なので、レビューが0件の商品も消えずに残る（件数0・平均 `NULL`） |
| 失敗すると | 別の関連の `Count` を2つ並べると、JOIN が掛け算になり、数が狂う（🔮の3） | `Avg` は、レビューが0件だと `None`。スキーマを `float` だけにすると 500 になるので、`float \| None` にした |

✅ 検証済み: Django 5.2.17 / MySQL 8.4.11

```text
  shop_product  shop_review (LEFT JOIN)  GROUP BY product
  ------------  -----------------------  ------------------------
  id=1          rating 4
  id=1          rating 5                 -> COUNT 2, AVG 4.5
  id=2          NULL (no review)         -> COUNT 0, AVG NULL
```

✅ 検証済み: ④の SQL と応答

見てほしいのは、JOIN で商品の行が**レビューの数だけ**に増えたあと、`GROUP BY` で商品1行に戻っている点です。

### 7-3. 🐍 Python注

新しい文法はありません。

### 7-4. 解説 — なぜこう設計するか

`for p in products: p.reviews.count()` と書いても、同じ数は出ます。でも、SQL は「一覧1本 + 商品の数」になります（2-4 の N+1 と同じ形）。`annotate()` なら、商品が何個でも1本です。

🧠 Django の考え方: 数える・足す・平均するは、行を Python に持ってこずに、DB にやらせる。結果だけを行に付けて受け取る。

### 7-5. 🏢 実務メモ

> 🏢 **実務メモ**: 公式ドキュメントは、`annotate()` に複数の集計を並べると「JOIN になるので結果が間違う」と注意している。`Count` なら `distinct=True` で避けられる。それ以外の集計を並べたいときは、サブクエリなど別の書き方が要る。
> 根拠: https://docs.djangoproject.com/en/5.2/topics/db/aggregation/#combining-multiple-aggregations

### 7-6. 🔮 予測 → 動作確認

1. 商品が2つある。`for p in Product.objects.all(): p.reviews.count()` と書くと、SQL は何本？
2. 星が 4・4・5 の3件なら、`rating_avg` は？ `4.333333333333333` になる？
3. 星3件・画像2枚の商品で、`annotate(rc=Count("reviews"), ic=Count("images"))` すると、`rc` と `ic` は？

<details><summary>答え</summary>

1. 3本。一覧で1本 + 商品ごとに `COUNT` が1本ずつ（検証済み）
2. `4.3333`。MySQL は割り算の結果を、小数点以下4桁までで返す（`div_precision_increment` の既定値が `4`）。Django はそれを `float` にする（検証済み）
   根拠: https://dev.mysql.com/doc/refman/8.4/en/server-system-variables.html#sysvar_div_precision_increment
3. どちらも `6`（3 × 2）。レビューと画像を両方 JOIN すると、行が掛け算で増えるから。`Count("reviews", distinct=True)` にすると `3` と `2` に戻る（検証済み）

</details>

### 7-7. ✅ 想起チェック

1. `annotate(review_count=Count("reviews"))` で付けた値は、Python のどこから読める？
2. レビューが0件の商品は、一覧から消える？ 平均は何になる？

<details><summary>答え</summary>

1. 各商品の属性（`product.review_count`）。スキーマも同じ名前で読める
2. 消えない（`LEFT OUTER JOIN` だから）。件数は `0`、平均は `None`（JSON では `null`）

</details>

### 7-8. 📇 まとめカード

この回で覚えることは1つだけ: **「〜ごとの件数・平均」は `annotate()` と `Count` / `Avg` で、SQL 1本のうちに DB に数えさせる。**

📒 用語集に追記: 集計関数（`Count` / `Avg`） / `annotate()` / `GROUP BY`

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第3部 ステップ8` — トランザクションのテスト


---

## 第3部-8: トランザクションのテスト

**❓ この回の問い**: 3-4 と 3-5 のテストは、2人を**順番に**通していた。だから、直す前のコードでも通ってしまった。本当に同時に走らせるテストは、なぜ今まで書けなかった？

**作るもの**: 2本のスレッドで同時に注文するテスト。注文の確認メールを「確定してから」送る仕組みと、そのテスト
**重要度**: 🟡 読めればよい — 毎回は書かない。でも、お金や在庫の処理には1本あると安心できる
**前ステップとの接続**: 3-4・3-5 で予告した「同時のテスト」を、ここで回収する。2-13 の `send_mail` を、注文の確定に使う

### 8-0. このステップの初出

**Django / Ninja**: `django_db(transaction=True)`, `transaction.on_commit()` / **Python**: `threading`, `lambda`

> 🧒 **かみくだくと**: ふだんのテスト（`@pytest.mark.django_db`）は、テスト全体を1つのトランザクションで包み、最後に**ロールバック**して片付けている。だから、テストの中の書き込みは一度も確定しない。`transaction=True` を付けると、包まずに**本当に確定**させ、テストの最後に全部の台帳を空にして片付ける。

> 🧒 **かみくだくと**: **on_commit()** は、「このトランザクションが確定したら、これをやって」という予約。取り消されたら、予約ごと捨てられる。

### 8-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

**① 確認メールを予約する**（`shop/api.py`）

import を1行足す（`from django.db import transaction` の上）

```python
from django.core.mail import send_mail
```

`place_order` の `order = Order.objects.create(...)` のすぐ下に足す

```python
        email = request.user.email
        if email:
            # 確認メールは、注文が確定（COMMIT）したあとに送る。取り消されたら送らない
            transaction.on_commit(
                lambda: send_mail(
                    subject=f"注文 {order.id} を受け付けました",
                    message=f"合計 {total} 円",
                    from_email=None,
                    recipient_list=[email],
                )
            )
```

✅ 検証済み: Django 5.2.17（ruff・mypy も通過）

予約は、在庫を確かめる**前**にしています。在庫が足りずに 409 で取り消されると、予約も捨てられます。わざと `send_mail(...)` を直接呼ぶ形にすると、409 なのにメールが1通出ました（検証済み）。

> 💡補足: `request.user.email` をいったん `email` に入れているのは、mypy のため。`lambda` の中では、上の `assert` で絞った「ログイン済み」の情報が、mypy に引き継がれない。

**② テストを書く**（`tests/test_transactions.py` 新規）

これまでの `auth_headers` は、ふだんのテスト用です。このファイルでは、ユーザーも中で作ります。

```python
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
```

✅ 検証済み: pytest-django 4.14.0（ruff・mypy も通過）

直す前のコード（3-3 の「読んで、引いて、書く」）に戻して10回走らせると、**10回とも落ちました**（`assert [201, 201] == [201, 409]`）。今のコードでは通ります。

続けて、要件だけ書きます（同じファイルに足す）。

1. 3-5 の2度押し: 同じ人の身分証で同時に2回注文すると、`[201, 400]`。在庫5は `4` になる
2. メールアドレスのある人が注文すると 201 で、`mailoutbox` に1通（宛先はその人）
3. 在庫0の商品を注文すると 409 で、`mailoutbox` は0通

<details><summary>解答例</summary>

```python
@pytest.mark.django_db(transaction=True)
def test_double_click_orders_once() -> None:
    category = Category.objects.create(name="本")
    book = Product.objects.create(name="Django 入門", price=Decimal("2980"), category=category)
    Inventory.objects.create(product=book, quantity=5)
    headers = login("alice")
    cart = Cart.objects.create(user=User.objects.get(username="alice"))
    CartItem.objects.create(cart=cart, product=book, quantity=1)

    statuses = post_at_the_same_time("/orders", [headers, headers])  # 同じ人が2回

    assert sorted(statuses) == [201, 400]  # 2回目は、空のカートを見る
    assert Inventory.objects.get(product=book).quantity == 4


def put_book_in_cart(username: str, stock: int) -> dict[str, str]:
    # 在庫 stock の本を、メールアドレスのある人のカートに1個入れる
    headers = login(username)
    user = User.objects.get(username=username)
    user.email = f"{username}@example.com"
    user.save()
    category = Category.objects.create(name="本")
    book = Product.objects.create(name="Django 入門", price=Decimal("2980"), category=category)
    Inventory.objects.create(product=book, quantity=stock)
    CartItem.objects.create(cart=Cart.objects.create(user=user), product=book, quantity=1)
    return headers


@pytest.mark.django_db(transaction=True)
def test_mail_is_sent_after_commit(mailoutbox) -> None:
    headers = put_book_in_cart("alice", stock=5)

    assert client.post("/orders", headers=headers).status_code == 201

    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == ["alice@example.com"]


@pytest.mark.django_db(transaction=True)
def test_no_mail_when_rolled_back(mailoutbox) -> None:
    headers = put_book_in_cart("alice", stock=0)  # 在庫なし

    assert client.post("/orders", headers=headers).status_code == 409

    assert len(mailoutbox) == 0  # 取り消された注文のメールは送られない
```

</details>

✅ 検証済み: pytest-django 4.14.0（`59 passed`。ruff・mypy も通過）

2度押しのテストも、鍵（`select_for_update()`）を外すと10回とも落ちました（`[201, 201]`）。これで 3-4・3-5 の ⏭️ を回収しました。

### 8-2. 🔬 仕組み解剖

| | `django_db(transaction=True)` | `transaction.on_commit()` |
| --- | --- | --- |
| 正式名称 | pytest-django の `django_db` マーカーの `transaction` 引数（Django の `TransactionTestCase` と同じ動き） | django.db.transaction.on_commit |
| いつ・誰が | ふだんは pytest-django がテストを `BEGIN` で包み、最後に `ROLLBACK`。`transaction=True` なら包まず、テストのあとで全部の台帳を空にする（MySQL では `DELETE FROM`） | 呼んだときは予約するだけ。いちばん外側の `atomic` が `COMMIT` した直後に、Django が予約を実行する。`ROLLBACK` なら捨てる |
| 発行される SQL | ふだんのテストの中の `atomic` は、`SAVEPOINT` … `ROLLBACK TO SAVEPOINT` になる（確認済み） | なし（Python の中の予約） |
| TS での対応物 | 対応物なし。Jest でも、DB を本当に確定させるかは自分で決める | 対応物なし（Django の機能）。Prisma の `$transaction` が終わってから書く処理が近い |
| なぜこの設計 | 包んで捨てるほうが速い。ただ、確定しないので、別のスレッドからは見えないし、`on_commit` も動かない | メールや外部への通知は、取り消せない。「確定したことだけを知らせる」ために、確定を待つ |
| 失敗すると | `transaction=True` を外すと、メールのテストは `assert 0 == 1` で落ちる（確認済み）。テストのたびに台帳を空にするので遅い | `atomic` の外で呼ぶと、その場ですぐ実行される。予約にならない |

✅ 検証済み: Django 5.2.17 / pytest-django 4.14.0 / MySQL 8.4.11

```text
  @pytest.mark.django_db                  @pytest.mark.django_db(transaction=True)
  --------------------------------------  ----------------------------------------
  BEGIN (pytest-django)
    atomic() -> SAVEPOINT                 atomic() -> BEGIN
    on_commit(send_mail) -> wait          on_commit(send_mail) -> wait
    end -> RELEASE SAVEPOINT              end -> COMMIT -> send_mail runs
  ROLLBACK (test data gone)               DELETE FROM all tables (test data gone)

  send_mail never runs                    other threads see the data
  other threads see nothing               slower
```

✅ 検証済み: 左は `CaptureQueriesContext` で取った SQL、右は②のテスト

見てほしいのは左の列です。テストの中の `atomic` は、外側の `BEGIN` の中の「しおり」（`SAVEPOINT`）になるだけで、`COMMIT` まで届きません。

### 8-3. 🐍 Python注

> 🐍 **Python注**: `threading.Thread(target=post, args=(h,))` は、`post(h)` を別のスレッドで動かす準備。`start()` で走り出し、`join()` で終わりを待つ。`(h,)` の `,` は「要素1つのタプル」の印。

> 🐍 **Python注**: `lambda: send_mail(...)` は、名前の無い小さな関数（TS の `() => sendMail(...)`）。その場では呼ばず、「あとで呼ぶもの」として渡す。

### 8-4. 解説 — なぜこう設計するか

ふだんのテストを全部 `transaction=True` にしないのは、遅いからです。テストのたびに、全部の台帳を空にします。この教材では、「同時に走らせる」と「確定を待つ」を試すテストだけを、別のファイルにまとめました。

🧠 Django の考え方: 取り消せないこと（メール・外部への通知）は、`on_commit()` で確定のあとに回す。確定を確かめるテストだけ、本当に確定させる。

### 8-5. 🏢 実務メモ

> 🏢 **実務メモ**: `on_commit()` が予約されたことだけを確かめたいなら、pytest-django の `django_capture_on_commit_callbacks` を使うと、`transaction=True` にせず（速いまま）予約を取り出して実行できる。
> 根拠: https://pytest-django.readthedocs.io/en/latest/helpers.html#django-capture-on-commit-callbacks

### 8-6. 🔮 予測 → 動作確認

1. メールのテストから `transaction=True` を外し、`@pytest.mark.django_db` だけにすると？
2. ふだんのテストで、在庫不足の注文（409）を送ると、SQL に `BEGIN` / `ROLLBACK` は出る？
3. `post` の中の `connection.close()` は何のため？

<details><summary>答え</summary>

1. 落ちる（`assert 0 == 1`）。テストの外側のトランザクションが確定しないので、予約したメールが送られない（検証済み）
2. 出ない。`SAVEPOINT` → `ROLLBACK TO SAVEPOINT` → `RELEASE SAVEPOINT` になる。外側は pytest-django が開いた `BEGIN` のまま（検証済み）
3. Django の DB 接続は、スレッドごとに1本ずつ開かれる。スレッドが終わっても、自分で閉じないと開いたまま残る

</details>

### 8-7. ✅ 想起チェック

1. ふだんのテストでは、なぜ別のスレッドから、テストで作った商品が見えない？
2. 確認メールを `on_commit()` で送るのはなぜ？

<details><summary>答え</summary>

1. テストの書き込みが、ロールバック前提の大きなトランザクションの中にあり、一度も確定しないから
2. 注文が取り消されたとき、メールだけ送られてしまわないようにするため

</details>

### 8-8. 📇 まとめカード

この回で覚えることは1つだけ: **確定してから起きること（`on_commit()`・別スレッドからの見え方）は、`transaction=True` のテストで確かめる。**

📒 用語集に追記: `transaction=True`（トランザクションのテスト） / `on_commit()` / セーブポイント

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第3部 ステップ9` — クエリの総点検


---

## 第3部-9: クエリの総点検

**❓ この回の問い**: 3-8 までで、注文は壊れずに確定できるようになった。最後に、「自分の注文履歴」を返す API を作る。注文 → 明細 → 商品と2段たどる一覧だと、SQL は何本になる？ そして、その SQL を MySQL はどう実行している？

**作るもの**: `GET /api/orders`（自分の注文履歴。明細に商品名つき）。SQL を3本に固定し、実行計画を読む
**重要度**: 🟡 読めればよい — 毎回は書かない。でも、一覧が遅いと言われたとき最初に見る場所
**前ステップとの接続**: 2-4 の `prefetch_related` を、入れ子（明細の中の商品）まで広げる

### 9-0. このステップの初出

**Django / Ninja**: `Prefetch` オブジェクト, `explain()` / **Python**: なし

> 🧒 **かみくだくと**: **Prefetch** は、`prefetch_related` の「取り方」を細かく指定する札。`Prefetch("items", queryset=...)` と書くと、明細を取る SQL に、さらに `select_related` などを足せる。

> 🧒 **かみくだくと**: **実行計画**（execution plan）は、MySQL が「この SQL をどう探すか」の段取り。`explain()` は、それを見せてもらう命令（SQL の `EXPLAIN`）。索引を使うのか、台帳を頭から全部読むのかが分かる。

> 🧒 **かみくだくと**: **索引**（index）は、本の巻末の索引と同じ。「`user_id` が 1 の行はここ」とすぐ引けるように、MySQL が別に持っている表。

### 9-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

**① 注文履歴の API**（`shop/api.py`）

import を1か所直す

```diff
-from django.db.models import Avg, Count, F
+from django.db.models import Avg, Count, F, Prefetch
```

`OrderItemOut` に1行足す（`product_id` の下）

```python
    name: str = Field(alias="product.name")  # 商品名（明細 → 商品とたどる）
```

`class OrderStatusIn` のすぐ上に追加

```python
@order_router.get("", response=list[OrderOut], auth=JWTAuth())
def list_orders(request: HttpRequest):
    assert request.user.is_authenticated
    return (
        Order.objects.filter(user=request.user)
        # 明細はまとめて1本で取る。そのとき、明細の商品も JOIN で一緒に取る
        .prefetch_related(Prefetch("items", queryset=OrderItem.objects.select_related("product")))
        .order_by("-created_at", "-id")  # 新しい注文から
    )
```

✅ 検証済み: django-ninja 1.7.1（ruff・mypy も通過）

**② SQL の本数を比べる**（注文3件 × 明細2行。`CaptureQueriesContext` で数えた）

| 書き方 | SQL の本数 | 内訳 |
| --- | --- | --- |
| 何も付けない | **10** | 注文1 + 明細3（注文ごと） + 商品6（明細ごと） |
| `.prefetch_related("items")` | **8** | 注文1 + 明細1 + 商品6（明細ごと） |
| `Prefetch("items", queryset=...select_related("product"))` | **2** | 注文1 + 明細と商品1 |

✅ 検証済み: Django 5.2.17 / MySQL 8.4.11

2-4 の `prefetch_related("tags")` だけでは、**明細の先の商品**が、明細1行ごとに1本ずつ取りに行かれます。`Prefetch` で、明細を取る SQL に `select_related("product")` を入れて、2本にまとめました。

```sql
SELECT ... FROM `shop_order` WHERE `shop_order`.`user_id` = 1
  ORDER BY `shop_order`.`created_at` DESC, `shop_order`.`id` DESC;
SELECT `shop_orderitem`.`id`, ..., `shop_product`.`id`, `shop_product`.`name`, ...
  FROM `shop_orderitem` INNER JOIN `shop_product` ON (`shop_orderitem`.`product_id` = `shop_product`.`id`)
  WHERE `shop_orderitem`.`order_id` IN (3, 2, 1);
```

✅ 検証済み: MySQL 8.4.11（列の一部を `...` に省略）

API として叩くと、これに身分証の確認（ユーザーの SELECT）1本が足されて、**3本**です。

**③ 実行計画を見る**

```bash
uv run python manage.py shell -c "
from shop.models import Order
print(Order.objects.filter(user_id=1).order_by('-created_at', '-id').explain())
print(Order.objects.filter(total=2980).explain())
"
```

```text
-> Sort: shop_order.created_at DESC, shop_order.id DESC  (cost=1.1 rows=1)
    -> Index lookup on shop_order using shop_order_user_id_00aba627_fk_accounts_user_id (user_id=1)  (cost=1.1 rows=1)

-> Filter: (shop_order.total = 2980.00)  (cost=1.1 rows=1)
    -> Table scan on shop_order  (cost=1.1 rows=1)
```

✅ 検証済み: MySQL 8.4.11（`cost` と `rows` は、台帳の行数で変わる。形は同じ）

読み方は、**下（字下げの深いほう）から上**です。

- 1つ目: `user_id` の**索引**で自分の注文だけを引き（`Index lookup`）、それを並べ替えている（`Sort`）
- 2つ目: `total` には索引が無いので、台帳を**頭から全部**読んで（`Table scan`）、合うものを残している（`Filter`）

`user_id` の索引は、自分で作っていません。Django は `ForeignKey` に、自動で索引を付けます。

**④ テスト**（`tests/test_order_history.py` 新規）

要件だけ書きます。

1. alice の注文2件と bob の注文1件がある。alice が `GET /orders` すると2件で、新しい順。明細に商品名が入っている
2. 注文が1件でも5件でも、SQL は3本（2-4 の `django_assert_num_queries` と `parametrize` を使う）

<details><summary>解答例</summary>

```python
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
```

</details>

✅ 検証済み: pytest-django 4.14.0（`62 passed`。3-8 のテストを4件とも書いた場合。ruff・mypy も通過）

`Prefetch(...)` を `"items"` だけに戻すと、`Expected to perform 3 queries but 5 were done` で落ちます（注文1件・明細2行のとき。検証済み）。

### 9-2. 🔬 仕組み解剖

| | `Prefetch` | `explain()` |
| --- | --- | --- |
| 正式名称 | django.db.models.Prefetch（Prefetch objects） | QuerySet.explain() |
| いつ・誰が | 一覧を評価したときに、Django が明細の SQL を1本（`order_id IN (...)`）送る。`queryset=` に書いた `select_related` が、その SQL の JOIN になる。受け取った明細を、Python が注文ごとに振り分ける | 呼んだときに Django が `EXPLAIN FORMAT=TREE SELECT ...` を送り、MySQL の段取りを文字列で返す。SQL 自体は実行しない |
| 発行される SQL | ②の2本目（`INNER JOIN shop_product ... WHERE order_id IN (3, 2, 1)`） | `EXPLAIN FORMAT=TREE SELECT ...` |
| TS での対応物 | Prisma の `include: { items: { include: { product: true } } }` が近い | 対応物なし（DB の機能）。Prisma にも無く、生 SQL で `EXPLAIN` を書く |
| なぜこの設計 | 「何を先に取るか」と「その取り方」を分けて書ける。並べ替えや絞り込みも `queryset=` に足せる | 「遅い」の理由は、SQL の本数か、1本の中身（索引を使っているか）のどちらか。本数は②、中身は③で見る |
| 失敗すると | `Prefetch` の `queryset=` に**別のモデル**（たとえば `Product.objects.all()`）を渡すと、`FieldError: Cannot resolve keyword 'order' into field.`（確認済み） | 索引が無い項目で絞ると `Table scan`。行が少ないうちは速いので、件数が増えてから遅くなる |

✅ 検証済み: Django 5.2.17 / MySQL 8.4.11

```text
  SQL 1: shop_order WHERE user_id = 1          -> orders 3, 2, 1
  SQL 2: shop_orderitem JOIN shop_product
         WHERE order_id IN (3, 2, 1)           -> 6 items (with product)
  Python: put each item under its order        -> order.items
```

✅ 検証済み: ②の SQL

見てほしいのは、SQL 2 の `IN (3, 2, 1)` です。SQL 1 で取った注文の id を、Django がまとめて渡しています。

### 9-3. 🐍 Python注

新しい文法はありません。

### 9-4. 解説 — なぜこう設計するか

一覧の API は、件数が増えたときに遅くなります。点検は2段です。まず**本数**（②。件数で増えていないか）、次に**1本の中身**（③。索引を使っているか）。本数はテストで固定しておけば、あとで誰かが項目を足して N+1 を作っても、テストが気づきます。

🧠 Django の考え方: SQL は Django が書いてくれる。でも、何本・どう実行されるかは、自分で見て確かめる。

### 9-5. 🏢 実務メモ

> 🏢 **実務メモ**: 公式ドキュメントの「データベースアクセスの最適化」は、まず索引など DB の基本の最適化を挙げ、`explain()` で SQL がどう実行されるかを確かめるよう勧めている。
> 根拠: https://docs.djangoproject.com/en/5.2/topics/db/optimization/#use-standard-db-optimization-techniques

### 9-6. 🔮 予測 → 動作確認

1. ②で、`Prefetch` をやめて `.prefetch_related("items__product")` と書いたら、SQL は何本？
2. `ForeignKey` を足しただけなのに、`user_id` に索引があった。誰が作った？
3. `place_order`（POST）の応答にも `name` が入るようになった。ここでの SQL は増えた？

<details><summary>答え</summary>

1. 3本（注文1 + 明細1 + 商品1。検証済み）。`__` でたどると、商品も `IN (...)` で別の1本になる。`Prefetch` + `select_related` なら JOIN で2本。どちらも件数で増えない
2. Django。`ForeignKey` には、自動で索引が付く（`db_index` の既定が `True`）
   根拠: https://docs.djangoproject.com/en/5.2/ref/models/fields/#foreignkey
3. 増えた。明細2行の注文で、11本 → 13本（明細ごとに商品を1本ずつ。検証済み）。注文1回の中の数本なので、ここでは直さない。直すなら、返す前に `Prefetch` 付きで取り直す

</details>

### 9-7. ✅ 想起チェック

1. `prefetch_related("items")` だけでは足りなかったのはなぜ？
2. `explain()` の結果に `Table scan` と出たら、何が起きている？

<details><summary>答え</summary>

1. 明細はまとめて取れたが、明細の先の商品を、明細1行ごとに取りに行っていたから
2. 索引を使わずに、台帳を頭から全部読んでいる。行が増えるほど遅くなる

</details>

### 9-8. 📇 まとめカード

この回で覚えることは1つだけ: **一覧の点検は2段。SQL の本数は `Prefetch` とテストで固定し、1本の中身は `explain()` で見る。**

📒 用語集に追記: `Prefetch` / 実行計画・`explain()` / 索引（インデックス）

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

これで第3部の本編は終わりです。分からなかった箇所は `# TODO: わからん` を残して、先に進んで大丈夫です。

▶ **次**: `M2: 第3部` — 白紙再現と宿題


---

## 第3部のまとめ（M2）— 白紙再現と宿題

ここまでで、EC 風の API（商品・カート・注文・レビュー）がそろいました。最後に、**思い出して書く練習**をして定着させます。

> ✍️ **翌日にやってください。** 書いた直後だと、短い記憶だけで書けてしまい、練習になりません。

### 1. 白紙再現（3段階から選ぶ）

| 段階 | やること | 判定 |
| --- | --- | --- |
| **Lv1 穴埋め** | 下のコードの `____` を埋める | `uv run pytest` が全部通る（`59 passed`。3-8 の残り3件を書いていれば `62 passed`） |
| **Lv2 ファイル単位** | `shop/api.py` を閉じ、白紙から書き直す（`shop/models.py` でもよい） | 同上。ruff・mypy も通る |
| **Lv3 構成から** | 要件だけを見て、どのファイルに何を書くかから組み立てる | 同上 |

> ✍️ まず Lv1 から。できたら次回 Lv2 に上げる。
> 思い出せなかった箇所に印を付け、**その箇所の 🔬 仕組み解剖だけ**読み返してください。

#### Lv1 穴埋め

`shop/api.py` を別名で退避（`cp shop/api.py /tmp/shop_api.py.bak`）してから、次のコードを**全文**貼って `____` を埋めます。同じ番号には同じ言葉が入ります。

```python
from datetime import datetime
from decimal import Decimal

from django.core.mail import send_mail
from django.db import transaction
from django.db.models import ____①____, ____②____, ____③____, ____④____
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Field, Router, Schema, Status
from ninja.errors import HttpError
from ninja_jwt.authentication import JWTAuth

from .models import Cart, CartItem, Inventory, Order, OrderItem, Product, Review

# 商品の API 一式。URL の頭（/products）は config/api.py で決める
router = Router()


class ProductOut(Schema):
    id: int
    name: str
    price: Decimal  # 金額。JSON では "1200.00" のような文字列になる
    category_id: int
    stock: int = Field(alias="inventory.quantity")  # 在庫の数（一対一の先をたどる）
    review_count: int  # レビューの件数（annotate で付け足した値）
    rating_avg: float | None  # 星の平均。レビューが無ければ null


def products_with_rating():
    # 在庫は JOIN で取り、レビューの件数と星の平均は MySQL に数えさせて、商品ごとに付け足す
    return Product.objects.select_related("inventory").____⑤____(
        review_count=____②____("reviews"), rating_avg=____①____("reviews__rating")
    )


@router.get("", response=list[ProductOut])
def list_products(request: HttpRequest):
    return products_with_rating().order_by("id")


@router.get("/{product_id}", response=ProductOut)
def get_product(request: HttpRequest, product_id: int):
    return get_object_or_404(products_with_rating(), id=product_id)


class ReviewIn(Schema):
    rating: int = Field(ge=1, le=5)  # 星は1〜5。外れたら 422
    comment: str = ""


class ReviewOut(Schema):
    id: int
    product_id: int
    user_id: int
    rating: int
    comment: str


@router.post("/{product_id}/reviews", response={201: ReviewOut}, auth=JWTAuth())
def create_review(request: HttpRequest, product_id: int, payload: ReviewIn):
    product = get_object_or_404(Product, id=product_id)
    assert request.user.is_authenticated
    if Review.objects.filter(product=product, user=request.user).____⑥____():
        raise HttpError(409, "この商品には、もうレビューを書いています")
    review = Review.objects.create(
        product=product, user=request.user, rating=payload.rating, comment=payload.comment
    )
    return Status(201, review)


# カートの API 一式。URL の頭（/cart）は config/api.py で決める
cart_router = Router()


class CartItemIn(Schema):
    product_id: int
    quantity: int = Field(default=1, ge=1)  # 省略したら1個。0以下は 422


class CartItemOut(Schema):
    product_id: int
    name: str = Field(alias="product.name")
    price: Decimal = Field(alias="product.price")
    quantity: int


class CartOut(Schema):
    items: list[CartItemOut]
    total: Decimal  # 合計金額


@cart_router.post("/items", response={201: CartItemOut}, auth=JWTAuth())
def add_to_cart(request: HttpRequest, payload: CartItemIn):
    product = get_object_or_404(Product, id=payload.product_id)
    assert request.user.is_authenticated
    # 自分のカートを取る。無ければ作る
    cart, _ = Cart.objects.____⑦____(user=request.user)
    # 同じ商品の行を取る。無ければ、入れた数で作る
    item, created = CartItem.objects.____⑦____(
        cart=cart, product=product, defaults={"quantity": payload.quantity}
    )
    if not created:
        # もう入っていたら、行は増やさずに数を足す。足し算は MySQL にさせる
        CartItem.objects.filter(id=item.id).____⑧____(quantity=____③____("quantity") + payload.quantity)
        item = CartItem.objects.get(id=item.id)  # 足したあとの数を読み直す

    return Status(201, item)


@cart_router.get("", response=CartOut, auth=JWTAuth())
def get_cart(request: HttpRequest):
    assert request.user.is_authenticated
    cart, _ = Cart.objects.____⑦____(user=request.user)
    items = cart.items.select_related("product").order_by("id")
    total = sum((item.product.price * item.quantity for item in items), Decimal("0"))
    return {"items": items, "total": total}


# 注文の API 一式。URL の頭（/orders）は config/api.py で決める
order_router = Router()


class OrderItemOut(Schema):
    product_id: int
    price: Decimal  # 買った時点の価格
    quantity: int
    name: str = Field(alias="product.name")  # 商品名（明細 → 商品とたどる）


class OrderOut(Schema):
    id: int
    total: Decimal
    created_at: datetime
    items: list[OrderItemOut]
    status: Order.Status  # "placed" / "shipped" / "completed" のどれか


@order_router.post("", response={201: OrderOut}, auth=JWTAuth())
def place_order(request: HttpRequest):
    assert request.user.is_authenticated
    # ここから下は「全部やるか、何もしないか」。途中で例外が出たら、全部取り消す
    with transaction.____⑨____():
        # カートの行に鍵をかけて読む。同じカートの2つ目の注文は、1つ目が終わるまでここで待つ
        cart = get_object_or_404(Cart.objects.____⑩____(), user=request.user)
        cart_items = list(cart.items.select_related("product"))
        if not cart_items:
            raise HttpError(400, "カートが空です")

        total = sum((ci.product.price * ci.quantity for ci in cart_items), Decimal("0"))
        order = Order.objects.create(user=request.user, total=total)

        email = request.user.email
        if email:
            # 確認メールは、注文が確定（COMMIT）したあとに送る。取り消されたら送らない
            transaction.____⑪____(
                lambda: send_mail(
                    subject=f"注文 {order.id} を受け付けました",
                    message=f"合計 {total} 円",
                    from_email=None,
                    recipient_list=[email],
                )
            )

        # 注文の明細を、INSERT 1本でまとめて作る
        OrderItem.objects.____⑫____(
            [
                OrderItem(
                    order=order, product=ci.product, price=ci.product.price, quantity=ci.quantity
                )
                for ci in cart_items
            ]
        )
        for ci in cart_items:
            # 在庫が足りているときだけ減らす。比べるのも引くのも、MySQL が UPDATE 1本の中でやる
            updated = Inventory.objects.filter(
                product=ci.product, ____⑬____=ci.quantity
            ).____⑧____(quantity=____③____("quantity") - ci.quantity)
            if updated == 0:
                # 例外で with を抜けると、上で作った注文と明細も無かったことになる
                raise HttpError(409, f"「{ci.product.name}」の在庫が足りません")

        cart.items.all().delete()  # カートを空にする

    return Status(201, order)


@order_router.get("", response=list[OrderOut], auth=JWTAuth())
def list_orders(request: HttpRequest):
    assert request.user.is_authenticated
    return (
        Order.objects.filter(user=request.user)
        # 明細はまとめて1本で取る。そのとき、明細の商品も JOIN で一緒に取る
        .prefetch_related(____④____("items", queryset=OrderItem.objects.select_related("product")))
        .order_by("-created_at", "-id")  # 新しい注文から
    )


class OrderStatusIn(Schema):
    status: Order.Status  # 3つ以外の値は 422


@order_router.patch("/{order_id}/status", response=OrderOut, auth=JWTAuth())
def change_order_status(request: HttpRequest, order_id: int, payload: OrderStatusIn):
    # 状態を進めるのはお店の人だけ（管理画面に入れるスタッフ）
    if not request.user.____⑭____:
        raise HttpError(403, "お店の人しか変えられません")
    order = get_object_or_404(Order, id=order_id)
    try:
        order.____⑮____(payload.status)  # 進んでよいかは、モデルが決める
    except ValueError as e:
        raise HttpError(409, str(e)) from e
    return order
```

⚠️ 未実行（穴埋め用のため、このままでは動かない。検証手順: 埋めたあと `uv run pytest`）

<details><summary>答え</summary>

① `Avg`（3-7）
② `Count`（3-7）
③ `F`（3-4）
④ `Prefetch`（3-9）
⑤ `annotate`（3-7）
⑥ `exists`（3-7。2-8 と同じ形）
⑦ `get_or_create`（3-2）
⑧ `update`（3-4）
⑨ `atomic`（3-3）
⑩ `select_for_update`（3-5）
⑪ `on_commit`（3-8）
⑫ `bulk_create`（3-3）
⑬ `quantity__gte`（3-4）
⑭ `is_staff`（3-6）
⑮ `change_status`（3-6）

埋めた全体は、第3部-9 までの `shop/api.py` と1文字違わず同じです（機械的に照合済み）。

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / django-ninja 1.7.1 / MySQL 8.4.11（`59 passed`）

</details>

終わったら、退避したファイルを戻してください（`cp /tmp/shop_api.py.bak shop/api.py`）。

#### Lv3 の要件

- 商品（カテゴリは第2部のもの）・在庫（一対一）・カート・注文・明細・レビューの台帳。金額は `DecimalField`。在庫・価格・星の範囲は DB の決まり（チェック制約）で守る
- カートは1人1つ、同じ商品は1行にまとめて数を足す。足し算は DB にさせる
- 注文の確定は「注文・明細・在庫を減らす・カートを空にする」を全部か何もしないか。在庫が足りなければ 409。最後の1個を2人が同時に買っても、2度押ししても壊れない
- 注文は「確定 → 発送済み → 完了」の順にしか進まない（スタッフだけ）。確定したら確認メール（取り消されたら送らない）
- 商品一覧に、レビューの件数と星の平均。注文履歴は、注文が何件でも SQL 3本

### 2. 宿題

**宿題はブランチを切ってやってください。** 第4部は、第3部の終わりの状態から始まるためです。

```bash
git switch -c homework-p3   # 宿題用のブランチを作って移る
# … 宿題をやる …
git switch main             # 終わったら main に戻る
```

⚠️ 未実行（Git の操作のため。検証手順: `git branch` で今いるブランチを確認）

#### Lv1 基礎確認 — 在庫のある商品だけ

**課題**: 商品一覧に `?in_stock=true` を足し、在庫が1以上の商品だけを返す。付けなければ、今までどおり全部。

**ヒント**: 2-11 と 第2部の宿題 Lv1 で、関連の先の項目を `__` でたどって絞り込んだ。一対一の先（在庫）でも同じ。「より大きい」は `gt`。

**判定基準**:
- `curl -s "http://127.0.0.1:8000/api/products?in_stock=true"` に、在庫0の商品が出ない
- 下の解答例のテストが通る

<details><summary>解答例</summary>

`shop/api.py`（`list_products` を、まるごと置き換える）

```python
@router.get("", response=list[ProductOut])
def list_products(request: HttpRequest, in_stock: bool = False):
    products = products_with_rating().order_by("id")
    if in_stock:
        # 一対一の先（在庫）の項目も、__ でたどって絞り込める
        products = products.filter(inventory__quantity__gt=0)
    return products
```

`tests/test_homework_p3_lv1.py`（新規）

```python
from decimal import Decimal

from ninja.testing import TestClient

from blog.models import Category
from config.api import api
from shop.models import Inventory, Product

client = TestClient(api)


def test_in_stock_only(db) -> None:
    category = Category.objects.create(name="本")
    for name, stock in [("ある", 3), ("ない", 0)]:
        product = Product.objects.create(name=name, price=Decimal("100"), category=category)
        Inventory.objects.create(product=product, quantity=stock)

    assert [p["name"] for p in client.get("/products?in_stock=true").json()] == ["ある"]
    assert len(client.get("/products").json()) == 2  # 付けなければ全部
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / django-ninja 1.7.1 / MySQL 8.4.11（ruff・mypy も通過）

`?in_stock=true` の `true` は、Ninja が `bool` に変えてくれます。`1`・`yes`・`on` でも `True` になり、`abc` なら 422 です（検証済み）。

根拠: https://docs.djangoproject.com/en/5.2/topics/db/queries/#lookups-that-span-relationships

</details>

#### Lv2 応用 — 注文を取り消す

**課題**: `POST /api/orders/{order_id}/cancel` を作る。ログイン必須で、自分の注文だけ。取り消せるのは「確定」のときだけで、在庫を買った数だけ戻し、状態を「キャンセル」にする。

**ヒント**:
- 状態を1つ足すのは 3-6 の `TextChoices`。`choices` を変えると、マイグレーションが1つできる
- 「取り消せるか」はお店の決まりなので、3-6 と同じくモデルのメソッドに書く
- 在庫を戻すのは 3-4 の `F()`。戻すのと状態を変えるのは、3-3 の `atomic` で1かたまりに
- 同じ注文の取り消しが同時に2回来たら？ 3-5 を思い出す

**判定基準**:
- 確定の注文を取り消すと 200 で `"status": "canceled"`、在庫が戻る
- 2回目と、発送済みの注文は 409（在庫は戻さない）。他人の注文は 404
- 同時に2回取り消しても、在庫は1回だけ戻る（`transaction=True` のテスト）
- 下の解答例のテストが通る

<details><summary>解答例</summary>

`shop/models.py`（import を2行置き換える）

```python
from django.db import models, transaction
from django.db.models import F, Q
```

`class Status` に1行足す（`COMPLETED` の下）

```python
        CANCELED = "canceled", "キャンセル"
```

`change_status` の下に追加

```python
    def cancel(self) -> None:
        # 取り消せるのは「確定」のときだけ。在庫を戻すのと状態を変えるのは、全部か何もしないか
        with transaction.atomic():
            # 同じ注文の取り消しが同時に来ても、在庫を2回戻さないように鍵をかけて読み直す
            order = Order.objects.select_for_update().get(id=self.id)
            if order.status != Order.Status.PLACED:
                raise ValueError(f"「{order.get_status_display()}」の注文は取り消せません")
            for item in order.items.all():
                Inventory.objects.filter(product_id=item.product_id).update(
                    quantity=F("quantity") + item.quantity
                )
            order.status = Order.Status.CANCELED
            order.save(update_fields=["status"])
        self.status = order.status
```

```bash
uv run python manage.py makemigrations shop   # 0006_alter_order_status.py ができる
uv run python manage.py migrate
```

`shop/api.py`（ファイルの最後に追加）

```python
@order_router.post("/{order_id}/cancel", response=OrderOut, auth=JWTAuth())
def cancel_order(request: HttpRequest, order_id: int):
    # 自分の注文に限る（他人の注文は、あるかどうかも教えずに 404）
    order = get_object_or_404(Order, id=order_id, user_id=request.user.id)
    try:
        order.cancel()
    except ValueError as e:
        raise HttpError(409, str(e)) from e
    return order
```

`tests/test_homework_p3_lv2.py`（新規。3-8 の `login` と `post_at_the_same_time` を使い回す）

```python
from decimal import Decimal

import pytest
from ninja.testing import TestClient

from accounts.models import User
from blog.models import Category
from config.api import api
from shop.models import Inventory, Order, OrderItem, Product
from tests.test_transactions import login, post_at_the_same_time

client = TestClient(api)


def make_order(user: User) -> Order:
    # 在庫3の本を2個買った「確定」の注文（在庫は買ったあとの3）
    category = Category.objects.create(name="本")
    book = Product.objects.create(name="Django 入門", price=Decimal("2980"), category=category)
    Inventory.objects.create(product=book, quantity=3)
    order = Order.objects.create(user=user, total=Decimal("5960"))
    OrderItem.objects.create(order=order, product=book, price=book.price, quantity=2)
    return order


def stock() -> int:
    return Inventory.objects.get().quantity


def test_cancel_returns_stock(user: User, auth_headers: dict[str, str]) -> None:
    order = make_order(user)

    res = client.post(f"/orders/{order.id}/cancel", headers=auth_headers)

    assert res.status_code == 200
    assert res.json()["status"] == "canceled"
    assert stock() == 5  # 3 + 2


def test_cannot_cancel_twice(user: User, auth_headers: dict[str, str]) -> None:
    order = make_order(user)
    client.post(f"/orders/{order.id}/cancel", headers=auth_headers)

    assert client.post(f"/orders/{order.id}/cancel", headers=auth_headers).status_code == 409
    assert stock() == 5  # 2回目は戻さない


def test_cannot_cancel_after_shipping(user: User, auth_headers: dict[str, str]) -> None:
    order = make_order(user)
    order.change_status(Order.Status.SHIPPED)

    assert client.post(f"/orders/{order.id}/cancel", headers=auth_headers).status_code == 409
    assert stock() == 3  # 戻さない


def test_other_users_order_is_404(auth_headers: dict[str, str]) -> None:
    order = make_order(User.objects.create_user(username="bob", password="pass1234"))

    assert client.post(f"/orders/{order.id}/cancel", headers=auth_headers).status_code == 404


@pytest.mark.django_db(transaction=True)
def test_double_cancel_at_the_same_time() -> None:
    headers = login("alice")
    order = make_order(User.objects.get(username="alice"))

    statuses = post_at_the_same_time(f"/orders/{order.id}/cancel", [headers, headers])

    assert sorted(statuses) == [200, 409]
    assert stock() == 5  # 在庫は1回だけ戻る
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / django-ninja 1.7.1 / MySQL 8.4.11（ruff・mypy も通過）

`select_for_update()` を外して `Order.objects.get(...)` にすると、同時のテストが10回とも落ちます（2回とも取り消せて、在庫が2回戻る）。`self.status` で確かめるだけでは、2つのリクエストがどちらも「確定」を読んでしまうからです。

</details>

#### Lv3 発展 — 商品ごとの売上

**課題**: スタッフ用の `GET /api/orders/sales` を作る。**完了した注文だけ**を数え、商品ごとに「売れた個数」と「売上金額（買った時点の価格 × 個数 の合計）」を、売上の多い順に返す。

**ヒント**:
- 集計は明細（`OrderItem`）から始める。注文の状態は `order__status` でたどれる
- 3-7 の `annotate()` は「行ごとに」付け足した。「商品ごとに」まとめるには、先に `values()` でまとめる単位を決める
- 合計は `Sum`。「価格 × 個数」は、`F()` 同士の掛け算を `Sum` に渡せる
- 付け足す名前に、モデルの項目と同じ名前（`quantity`）を使うと、どうなる？

**判定基準**:
- 完了2件・確定1件の注文があるとき、完了した2件ぶんだけが集計される
- 値上げの前後で買った明細は、それぞれ買った時点の価格で足される
- お客は 403
- 下の解答例のテストが通る

<details><summary>解答例</summary>

`shop/api.py`（import の `Prefetch` の後ろに `Sum` を足し、ファイルの最後に追加）

```diff
-from django.db.models import Avg, Count, F, Prefetch
+from django.db.models import Avg, Count, F, Prefetch, Sum
```

```python
class SalesOut(Schema):
    product_id: int
    name: str
    sold: int  # 売れた個数
    amount: Decimal  # 売上金額（買った時点の価格 × 個数 の合計）


@order_router.get("/sales", response=list[SalesOut], auth=JWTAuth())
def sales(request: HttpRequest):
    if not request.user.is_staff:
        raise HttpError(403, "お店の人しか見られません")
    return (
        OrderItem.objects.filter(order__status=Order.Status.COMPLETED)  # 完了した注文だけ
        .values("product_id", name=F("product__name"))  # 商品ごとにまとめる
        # 付け足す名前を quantity にすると、明細の項目 quantity とぶつかる
        .annotate(sold=Sum("quantity"), amount=Sum(F("price") * F("quantity")))
        .order_by("-amount")  # よく売れた順
    )
```

`tests/test_homework_p3_lv3.py`（新規）

```python
from decimal import Decimal

from ninja.testing import TestClient

from accounts.models import User
from blog.models import Category
from config.api import api
from shop.models import Order, OrderItem, Product
from tests.test_order_status import staff_headers  # noqa: F401

client = TestClient(api)


def test_sales_by_product(user: User, staff_headers: dict[str, str]) -> None:  # noqa: F811
    category = Category.objects.create(name="本")
    book = Product.objects.create(name="Django 入門", price=Decimal("3000"), category=category)
    note = Product.objects.create(name="Python ノート", price=Decimal("500"), category=category)
    for status, items in [
        (Order.Status.COMPLETED, [(book, Decimal("2980"), 1), (note, Decimal("500"), 2)]),
        (Order.Status.COMPLETED, [(book, Decimal("3000"), 2)]),  # 値上げ後に買った
        (Order.Status.PLACED, [(book, Decimal("3000"), 5)]),  # まだ完了していない
    ]:
        order = Order.objects.create(user=user, total=Decimal("0"), status=status)
        for product, price, quantity in items:
            OrderItem.objects.create(order=order, product=product, price=price, quantity=quantity)

    body = client.get("/orders/sales", headers=staff_headers).json()

    assert body == [
        {"product_id": book.id, "name": "Django 入門", "sold": 3, "amount": "8980.00"},
        {"product_id": note.id, "name": "Python ノート", "sold": 2, "amount": "1000.00"},
    ]


def test_sales_is_for_staff(auth_headers: dict[str, str]) -> None:
    assert client.get("/orders/sales", headers=auth_headers).status_code == 403
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / django-ninja 1.7.1 / MySQL 8.4.11（Lv1〜Lv3 を全部入れて `67 passed`。ruff・mypy も通過）

```sql
SELECT `shop_orderitem`.`product_id` AS `product_id`, `shop_product`.`name` AS `name`,
       SUM(`shop_orderitem`.`quantity`) AS `sold`,
       SUM((`shop_orderitem`.`price` * `shop_orderitem`.`quantity`)) AS `amount`
FROM `shop_orderitem`
INNER JOIN `shop_order` ON (`shop_orderitem`.`order_id` = `shop_order`.`id`)
INNER JOIN `shop_product` ON (`shop_orderitem`.`product_id` = `shop_product`.`id`)
WHERE `shop_order`.`status` = 'completed'
GROUP BY 1, 2 ORDER BY 4 DESC;
```

✅ 検証済み: MySQL 8.4.11（`CaptureQueriesContext` で取得）

`sold` を `quantity` という名前にすると、`F("quantity")` が明細の項目ではなく、いま付け足した合計を指してしまいます。`FieldError: Cannot compute Sum(...): ... is an aggregate` で止まります（検証済み）。

根拠: https://docs.djangoproject.com/en/5.2/topics/db/aggregation/#values

</details>

### 3. 第3部の終わりに

**ここまでで、できるようになったこと**
- お金は `DecimalField`、「0以上」「1つだけ」はチェック制約と一意制約で、DB に守らせる設計ができる
- いくつもの書き込みを `transaction.atomic` で1かたまりにし、失敗したら全部取り消せる
- 「同時に来たら？」を実際に起こし、`F()` と `select_for_update()` で直し、`transaction=True` のテストで固定できる
- 業務ルールをモデルのメソッドに置き、`TextChoices` で状態を管理できる
- `annotate()` で集計し、`Prefetch` と `explain()` で SQL の本数と中身を点検できる

**ここで止めても成果物になります。** 手元には、ブログ API に加えて「カート・注文・在庫・レビューの付いた EC 風の API」があり、同時に注文されても壊れないことがテストで確かめられています。

**第4部で増えるもの**
- React（Vite）の画面から、この API を呼ぶ（CORS の設定）
- Ninja の OpenAPI から、TypeScript の型を作る
- ログイン・一覧・カートと注文の画面（3〜4画面）

第4部に進むかどうかは、ここで決めてください。
分からないまま残った箇所は、`# TODO: わからん` の印だけ見返せば十分です。

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第4部 ステップ1` — CORS ／ または `MP: url-shortening-service`
