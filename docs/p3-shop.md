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
