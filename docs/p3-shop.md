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
