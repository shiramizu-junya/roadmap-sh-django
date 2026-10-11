# 第2部 — ブログ API として完成させる

> 第1部と同じく、1周目で全部分からなくて大丈夫です。
> 分からない箇所には `# TODO: わからん` と残して、先に進んでください。

---

## 第2部-1: API をアプリごとに分ける

**❓ この回の問い**: API は `config/api.py` 1つ。機能が増えたらどうなるか？

**作るもの**: 記事の API を `blog/api.py` へ。pre-commit を入れ、接続情報を `.env` へ
**重要度**: 🔴 毎日使う — 以降、アプリごとに `api.py` を持つ
**前ステップとの接続**: 第1部の `config/api.py` を分ける（テストはそのまま）

### 1-0. このステップの初出

**Django / Ninja**: `Router`（と `add_router`） / **Python**: なし

> 🧒 **かみくだくと**: **Router** は窓口の「部署」。記事の窓口一式をまとめ、本庁（`NinjaAPI`）に差し込む。
> **pre-commit** は、コミット直前に検査を自動で走らせる道具。

### 1-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

前提: 環境準備の §2.4 が済んでいること。

**① Router に分ける**

`blog/api.py`（新規・全文。中身は第1部とほぼ同じ）

```python
from datetime import datetime

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Field, Router, Schema, Status

from .models import Post

# 記事の API 一式。URL の頭（/posts）は config/api.py で決める
router = Router()


class PostIn(Schema):
    title: str = Field(max_length=200)
    body: str


class PostPatch(Schema):
    title: str | None = Field(default=None, max_length=200)
    body: str | None = None


class PostOut(Schema):
    id: int
    title: str
    body: str
    created_at: datetime


@router.get("", response=list[PostOut])
def list_posts(request: HttpRequest):
    return Post.objects.all()


@router.post("", response={201: PostOut})
def create_post(request: HttpRequest, payload: PostIn):
    post = Post.objects.create(title=payload.title, body=payload.body)
    return Status(201, post)


@router.get("/{post_id}", response=PostOut)
def get_post(request: HttpRequest, post_id: int):
    return get_object_or_404(Post, id=post_id)


@router.patch("/{post_id}", response=PostOut)
def update_post(request: HttpRequest, post_id: int, payload: PostPatch):
    post = get_object_or_404(Post, id=post_id)
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    for name, value in changes.items():
        setattr(post, name, value)
    post.save()
    return post


@router.delete("/{post_id}", response={204: None})
def delete_post(request: HttpRequest, post_id: int):
    post = get_object_or_404(Post, id=post_id)
    post.delete()
    return Status(204, None)
```

`config/api.py`（全文。入口だけになる）

```python
from ninja import NinjaAPI

from blog.api import router as posts_router

api = NinjaAPI()

# アプリごとの Router を、URL の頭を決めて差し込む
api.add_router("/posts", posts_router, tags=["posts"])
```

```bash
uv run pytest -q   # 1-12 のテストは書き換えない
```

```text
4 passed
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / django-ninja 1.7.1 / MySQL 8.4.11（URL は `/api/posts` のまま。ruff・mypy も通過）

**② 接続情報を `.env` へ**

`.env`（追記）

```bash
DJANGO_DEBUG=1
DB_NAME=blog
DB_USER=django
DB_PASSWORD=django
DB_ROOT_PASSWORD=rootpass
DB_HOST=127.0.0.1
DB_PORT=3307
```

`config/settings.py`（差分）

```python
# 開発中だけ .env で DJANGO_DEBUG=1 にする。書き忘れたら False（安全側）
DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ["DB_NAME"],
        "USER": os.environ["DB_USER"],
        "PASSWORD": os.environ["DB_PASSWORD"],
        "HOST": os.environ["DB_HOST"],
        "PORT": os.environ["DB_PORT"],
        "OPTIONS": {"charset": "utf8mb4"},
    }
}
```

`compose.yaml`（`environment` と `ports` を差し替え）

```yaml
    environment:
      # 値は同じフォルダの .env から読む（docker compose が自動で読む）
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
      MYSQL_DATABASE: ${DB_NAME}
      MYSQL_USER: ${DB_USER}
      MYSQL_PASSWORD: ${DB_PASSWORD}
    ports:
      - "127.0.0.1:${DB_PORT}:3306"
```

`.env.example`（新規。Git に入れる見本）

```bash
# .env の見本。cp .env.example .env でコピーし、値を書き換えて使う
DJANGO_SECRET_KEY='ここに get_random_secret_key() の出力を入れる'
DJANGO_DEBUG=1
DB_NAME=blog
DB_USER=django
DB_PASSWORD=django
DB_ROOT_PASSWORD=rootpass
DB_HOST=127.0.0.1
DB_PORT=3307
```

```bash
docker compose config | grep MYSQL_   # .env の値が入ったか確かめる
docker compose up -d --wait           # 値は同じなので、データはそのまま
uv run python manage.py check
```

✅ 検証済み: Docker 29.8 / MySQL 8.4.11（値を変えずに作り直しても、既存の記事はそのまま読めた）

**③ pre-commit を入れる**

```bash
uv add --dev pre-commit
uv run pre-commit install   # .git/hooks に仕掛けを置く（最初の1回だけ）
```

`.pre-commit-config.yaml`（新規・全文）

```yaml
# コミットの直前に、自動で検査を走らせる設定
# 道具はプロジェクトに入っているもの（uv run）をそのまま使う
repos:
  - repo: local
    hooks:
      - id: ruff-check
        name: ruff check（書き方の誤り。直せるものは直す）
        entry: uv run ruff check --fix
        language: system
        types: [python]
      - id: ruff-format
        name: ruff format（見た目を揃える）
        entry: uv run ruff format
        language: system
        types: [python]
      - id: mypy
        name: mypy（型の食い違い）
        entry: uv run mypy .
        language: system
        types: [python]
        pass_filenames: false
```

```text
ruff check（書き方の誤り。直せるものは直す）.............................Passed
ruff format（見た目を揃える）............................................Passed
mypy（型の食い違い）.....................................................Passed
```

✅ 検証済み: pre-commit 4.6.2（`git commit` 時の出力）

### 1-2. 🔬 仕組み解剖

| | `Router` と `add_router` |
| --- | --- |
| 正式名称 | `ninja.Router` / `NinjaAPI.add_router` |
| いつ・誰が | 起動時に、関数一式を `/posts` の下に登録する |
| TS での対応物 | Express の `Router()` と `app.use("/posts", router)` |
| なぜこの設計 | API はアプリの中、URL の頭は入口で決める |
| 失敗すると | 差し込み忘れは 404 |

```text
GET /api/posts/1（窓口に来た人）
  └→ config/urls.py   "api/"   → NinjaAPI（本庁の入口）
       └→ config/api.py   "/posts" → posts_router（記事の部署）
            └→ blog/api.py   "/{post_id}" → get_post（担当職員）
```

✅ 検証済み: django-ninja 1.7.1（OpenAPI の操作名も `blog_api_get_post` に変わる）

見てほしいのは、**URL が3か所の継ぎ足し**である点。

### 1-3. 🐍 Python注

（この回は新しい文法なし）

### 1-4. 解説 — なぜこう設計するか

テストを書き換えずに通れば、動きは変わっていません。1-12 の成果です。

🧠 Django の考え方: アプリが部品を持ち、プロジェクトは差し込むだけ。

### 1-5. 🏢 実務メモ

> 🏢 **実務メモ**: 環境ごとに変わる値は環境変数に置き、見本を `.env.example` で共有する。
> 根拠: https://12factor.net/ja/config

### 1-6. 🔮 予測 → 動作確認

1. `DJANGO_DEBUG=`（空）を付けて起動すると、`DEBUG` は？
2. `.env` の `DB_NAME` を消すと？（試したら戻す）
3. 型を間違えた関数を足して `git commit` すると？（試したら戻す）

<details><summary>答え</summary>

1. `False`。外の環境変数が `.env` より優先され、空は `"1"` ではない
2. `KeyError: 'DB_NAME'` で起動しない
3. mypy が止め、コミットされない

</details>

### 1-7. ✅ 想起チェック

1. `/api`・`/posts`・`/{post_id}` は、それぞれどのファイルで決まる？

<details><summary>答え</summary>

1. `config/urls.py` ／ `config/api.py` ／ `blog/api.py`

</details>

### 1-8. 📇 まとめカード

この回で覚えることは1つだけ: **API はアプリごとの Router に置き、`add_router` で差し込む。**

📒 用語集に追記: Router / pre-commit / `.env.example`

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第2部 ステップ2` — カテゴリ（多対一）

---

## 第2部-2: カテゴリ（多対一）

**❓ この回の問い**: 記事を「日記」「技術」と分類するには、台帳をどうつなぐか？

**作るもの**: `Category` を作り、記事に1つのカテゴリを付ける
**重要度**: 🔴 毎日使う — 台帳をつなぐ基本の形
**前ステップとの接続**: 2-1 の `blog/api.py` にカテゴリを足す

### 2-0. このステップの初出

**Django / Ninja**: `ForeignKey`, `on_delete` / **Python**: なし

> 🧒 **かみくだくと**: **多対一**は「記事は1つのカテゴリに属し、カテゴリには多くの記事」の関係。
> **外部キー**は、別の台帳の `id` を書いておく列。

### 2-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

`blog/models.py`（差分。`Post` の上に `Category` を足し、`Post` に1項目足す）

```python
class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.name


class Post(models.Model):
    # （既存の項目はそのまま）
    # 多対一: 1つの記事は1つのカテゴリに属する（カテゴリには多くの記事）
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,  # 記事が残っているカテゴリは消せない
        null=True,  # 既存の記事にはカテゴリが無いので、空を許す
        blank=True,  # 管理画面の入力欄も空でよい
    )
```

`blog/admin.py`（差分）: `Category` も import し、`admin.site.register(Category)` を足す。

```bash
uv run python manage.py makemigrations
uv run python manage.py sqlmigrate blog 0002
uv run python manage.py migrate
```

```sql
CREATE TABLE `blog_category` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `name` varchar(50) NOT NULL UNIQUE);
ALTER TABLE `blog_post` ADD COLUMN `category_id` bigint NULL , ADD CONSTRAINT `blog_post_category_id_c326dbf8_fk_blog_category_id` FOREIGN KEY (`category_id`) REFERENCES `blog_category`(`id`);
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / MySQL 8.4.11（`+ Create model Category` / `+ Add field category to post`）

`blog/api.py`（差分）

```python
from .models import Category, Post


class PostIn(Schema):
    title: str = Field(max_length=200)
    body: str
    category_id: int | None = None  # 省略したらカテゴリなし


class PostOut(Schema):
    id: int
    title: str
    body: str
    created_at: datetime
    category_id: int | None


@router.post("", response={201: PostOut})
def create_post(request: HttpRequest, payload: PostIn):
    category = None
    if payload.category_id is not None:
        # 無いカテゴリを指定されたら 404（DB の外部キーで弾かれる前に止める）
        category = get_object_or_404(Category, id=payload.category_id)
    post = Post.objects.create(title=payload.title, body=payload.body, category=category)
    return Status(201, post)
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / django-ninja 1.7.1（ruff・mypy も通過）

`tests/test_categories.py`（新規。`# TODO` を埋める）

```python
import pytest
from django.db.models import ProtectedError
from ninja.testing import TestClient

from blog.models import Category, Post
from config.api import api

client = TestClient(api)


@pytest.mark.django_db
def test_create_post_with_category() -> None:
    category = Category.objects.create(name="日記")
    res = client.post("/posts", json={"title": "t", "body": "b", "category_id": category.id})
    # TODO: ステータスが 201 で、応答の category_id が category.id であること


@pytest.mark.django_db
def test_unknown_category_is_404() -> None:
    res = client.post("/posts", json={"title": "t", "body": "b", "category_id": 999})
    # TODO: ステータスが 404 で、記事が1件も保存されていないこと


@pytest.mark.django_db
def test_category_in_use_cannot_be_deleted() -> None:
    category = Category.objects.create(name="日記")
    Post.objects.create(title="t", body="b", category=category)

    with pytest.raises(ProtectedError):  # この中で ProtectedError が起きれば合格
        category.delete()
```

⚠️ 未実行（穴埋め用のため。検証手順: 埋めたあと `uv run pytest -q` が `7 passed`）

<details><summary>解答例</summary>

```python
    assert res.status_code == 201
    assert res.json()["category_id"] == category.id
```

```python
    assert res.status_code == 404
    assert Post.objects.count() == 0
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / MySQL 8.4.11（`7 passed`）

</details>

### 2-2. 🔬 仕組み解剖

| | `ForeignKey` | `on_delete` |
| --- | --- | --- |
| 正式名称 | 外部キーのフィールド | 参照先が消されるときの決まり |
| いつ・誰が | マイグレーションで、列 `category_id` と外部キー制約を作る | 削除のとき、**Django が**参照する行を調べて動く |
| TS での対応物 | 対応物なし（ORM の機能） | 対応物なし |
| なぜこの設計 | `id` でつなぐので、名前を変えても壊れない | 消してよいかはデータの意味で決まる |
| 失敗すると | 無い `id` は MySQL が拒否（1452） | `PROTECT` なら `ProtectedError` |

```text
カテゴリ「日記」(id=1) を消す
  ├─ PROTECT … 参照する記事を探す → あれば ProtectedError（何も消えない）
  └─ CASCADE … 参照する記事を先に消す → カテゴリを消す
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / MySQL 8.4.11（どちらも shell で実行）

見てほしいのは、上の SQL に **`ON DELETE` が無い**こと。消し方は Django が決めています。

> ✅ **回収（1-11）**: `CASCADE` だと `delete()` は `(3, {'blog.Post': 2, 'blog.Category': 1})` を返す。記事も消える。

### 2-3. 🐍 Python注

（この回は新しい文法なし）

### 2-4. 解説 — なぜこう設計するか

カテゴリと一緒に記事が消える（`CASCADE`）と困るので、`PROTECT` にしました。

🧠 Django の考え方: 参照先が消えたときの扱いを、モデルに必ず書かせる。

### 2-5. 🏢 実務メモ

> 🏢 **実務メモ**: `on_delete` は省略できない。`CASCADE`・`PROTECT`・`SET_NULL` などから選ぶ。
> 根拠: https://docs.djangoproject.com/en/5.2/ref/models/fields/#django.db.models.ForeignKey.on_delete

### 2-6. 🔮 予測 → 動作確認

1. `category_id: 999`（無いカテゴリ）で POST すると？
2. 404 の確認を書かずに、無い `category_id` で保存したら？

<details><summary>答え</summary>

1. 404。記事は保存されない
2. 500。MySQL の `IntegrityError (1452, ... a foreign key constraint fails ...)`（検証済み）

</details>

### 2-7. ✅ 想起チェック

1. `on_delete` を実際に動かしているのは MySQL か Django か？

<details><summary>答え</summary>

1. Django（SQL に `ON DELETE` が無い）

</details>

### 2-8. 📇 まとめカード

この回で覚えることは1つだけ: **`ForeignKey` で台帳をつなぎ、消すときの扱いを `on_delete` で決める。**

📒 用語集に追記: 多対一 / 外部キー / on_delete

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第2部 ステップ3` — タグ（多対多）
