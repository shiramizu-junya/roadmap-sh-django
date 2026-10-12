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
# --force-exclude: pyproject.toml の除外（migrations）を、渡されたファイルにも効かせる
repos:
  - repo: local
    hooks:
      - id: ruff-check
        name: ruff check（書き方の誤り。直せるものは直す）
        entry: uv run ruff check --fix --force-exclude
        language: system
        types: [python]
      - id: ruff-format
        name: ruff format（見た目を揃える）
        entry: uv run ruff format --force-exclude
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

---

## 第2部-3: タグ（多対多）

**❓ この回の問い**: カテゴリは1つだった。記事に**いくつも**付けるタグは、どうつなぐ？

**作るもの**: 記事に複数のタグを付け、応答にタグを入れ子で返す
**重要度**: 🔴 毎日使う — タグ・お気に入りなどでよく出る
**前ステップとの接続**: 2-2 に続き、もう1つのつなぎ方を足す

### 3-0. このステップの初出

**Django / Ninja**: `ManyToManyField`（と `.set()`）, 入れ子の `Schema` / **Python**: なし

> 🧒 **かみくだくと**: **多対多**は「記事に複数のタグ、タグに複数の記事」の関係。
> 間に、組を書き並べる**つなぎの台帳**が要る。

### 3-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

`blog/models.py`（差分。`Post` の上に `Tag` を足し、`Post` に1項目足す）

```python
class Tag(models.Model):
    name = models.CharField(max_length=30, unique=True)

    def __str__(self) -> str:
        return self.name


class Post(models.Model):
    # （既存の項目はそのまま）
    # 多対多: 1つの記事に複数のタグ、1つのタグに複数の記事
    tags = models.ManyToManyField(Tag, blank=True)
```

`blog/admin.py`（差分）: `Tag` も import し、`admin.site.register(Tag)` を足す。

```bash
uv run python manage.py makemigrations
SQL_LOG=0 uv run python manage.py sqlmigrate blog 0003
uv run python manage.py migrate
```

```sql
CREATE TABLE `blog_tag` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `name` varchar(30) NOT NULL UNIQUE);
CREATE TABLE `blog_post_tags` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `post_id` bigint NOT NULL, `tag_id` bigint NOT NULL);
ALTER TABLE `blog_post_tags` ADD CONSTRAINT `blog_post_tags_post_id_tag_id_4925ec37_uniq` UNIQUE (`post_id`, `tag_id`);
ALTER TABLE `blog_post_tags` ADD CONSTRAINT `blog_post_tags_post_id_a1c71c8a_fk_blog_post_id` FOREIGN KEY (`post_id`) REFERENCES `blog_post` (`id`);
ALTER TABLE `blog_post_tags` ADD CONSTRAINT `blog_post_tags_tag_id_0875c551_fk_blog_tag_id` FOREIGN KEY (`tag_id`) REFERENCES `blog_tag` (`id`);
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / MySQL 8.4.11（`+ Create model Tag` / `+ Add field tags to post`）

`blog/api.py`（差分）

```python
from .models import Category, Post, Tag


class PostIn(Schema):
    title: str = Field(max_length=200)
    body: str
    category_id: int | None = None  # 省略したらカテゴリなし
    tag_ids: list[int] = []  # 付けるタグの id。省略したらタグなし


class TagOut(Schema):
    id: int
    name: str


class PostOut(Schema):
    id: int
    title: str
    body: str
    created_at: datetime
    category_id: int | None
    tags: list[TagOut]  # 入れ子: 記事の中にタグの一覧を入れて返す


@router.post("", response={201: PostOut})
def create_post(request: HttpRequest, payload: PostIn):
    category = None
    if payload.category_id is not None:
        category = get_object_or_404(Category, id=payload.category_id)
    # 無いタグが1つでもあれば 404（記事を作る前に確かめる）
    tags = [get_object_or_404(Tag, id=tag_id) for tag_id in payload.tag_ids]
    post = Post.objects.create(title=payload.title, body=payload.body, category=category)
    post.tags.set(tags)  # つなぎの台帳（blog_post_tags）に行を入れる
    return Status(201, post)
```

管理画面でタグを2つ作ってから試します。

```bash
curl -s -X POST http://127.0.0.1:8000/api/posts \
  -H 'Content-Type: application/json' -d '{"title": "タグ付き", "body": "b", "tag_ids": [1, 2]}'
```

```text
{"id": 1, "title": "タグ付き", "body": "b", "created_at": "2026-10-12T07:46:59.333Z", "category_id": null, "tags": [{"id": 1, "name": "python"}, {"id": 2, "name": "django"}]}
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / django-ninja 1.7.1 / MySQL 8.4.11（ruff・mypy も通過。`id` は手元のデータで変わる）

`.set()` が出す SQL（runserver のログ）:

```sql
SELECT `blog_tag`.`id` AS `id` FROM `blog_tag` INNER JOIN `blog_post_tags` ON (`blog_tag`.`id` = `blog_post_tags`.`tag_id`) WHERE `blog_post_tags`.`post_id` = 1
INSERT IGNORE INTO `blog_post_tags` (`post_id`, `tag_id`) VALUES (1, 1), (1, 2)
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / MySQL 8.4.11（前後に `BEGIN` / `COMMIT` が付く）

**テスト**（3回目なので要件だけ）: `tests/test_tags.py` に次の2件を書く。
- タグ2つを付けて作ると 201。応答の `tags` の名前が付けた2つと一致
- 無いタグ `999` は 404。記事は保存されない

<details><summary>解答例</summary>

```python
import pytest
from ninja.testing import TestClient

from blog.models import Post, Tag
from config.api import api

client = TestClient(api)


@pytest.mark.django_db
def test_create_post_with_tags() -> None:
    python = Tag.objects.create(name="python")
    django = Tag.objects.create(name="django")

    res = client.post("/posts", json={"title": "t", "body": "b", "tag_ids": [python.id, django.id]})
    assert res.status_code == 201
    # 並び順は保証されないので、並べ替えてから比べる
    assert sorted(tag["name"] for tag in res.json()["tags"]) == ["django", "python"]


@pytest.mark.django_db
def test_unknown_tag_is_404_and_nothing_saved() -> None:
    res = client.post("/posts", json={"title": "t", "body": "b", "tag_ids": [999]})
    assert res.status_code == 404
    assert Post.objects.count() == 0
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / MySQL 8.4.11（`9 passed` を3回続けて確認）

</details>

### 3-2. 🔬 仕組み解剖

| | `ManyToManyField` | 入れ子の `Schema` |
| --- | --- | --- |
| 正式名称 | 多対多のフィールド（`.set()` で付け替える） | Schema の中に Schema のリストを置く |
| いつ・誰が | マイグレーションで、つなぎの台帳を作る（`blog_post` の列は増えない） | 応答を作るとき、`post.tags` から中身を取り出す |
| TS での対応物 | 対応物なし（ORM の機能） | 型 `{ tags: { id: number; name: string }[] }` |
| なぜこの設計 | 1列に値は1つなので、組を別の台帳に並べる | 記事とタグを一度に渡せる |
| 失敗すると | 同じ組は `UNIQUE` で1行のまま | 取り出しで SQL が増える（3-6） |

```text
blog_post            blog_post_tags（つなぎ）   blog_tag
id │ title           post_id │ tag_id           id │ name
 1 │ タグ付き ───→      1    │   1   ───→        1 │ python
                        1    │   2   ───→        2 │ django
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / MySQL 8.4.11

見てほしいのは、**記事とタグの間にもう1つ台帳がある**点。

### 3-3. 🐍 Python注

（この回は新しい文法なし）

### 3-4. 解説 — なぜこう設計するか

`ForeignKey` は相手の `id` を1つ書く列でした。多対多は1つに決まらないので、組を行で並べます。

🧠 Django の考え方: つなぎの台帳は Django が隠し、書く側は `post.tags` だけ扱う。

### 3-5. 🏢 実務メモ

> 🏢 **実務メモ**: `.set()` は今の組と比べ、足りない分を足して余分を消す。
> 根拠: https://docs.djangoproject.com/en/5.2/ref/models/relations/#django.db.models.fields.related.RelatedManager.set

### 3-6. 🔮 予測 → 動作確認

1. 記事が3件ある一覧 `GET /api/posts` では、SQL は何本？
2. タグを `[python, django]` の順で付けたら、応答もその順？

<details><summary>答え</summary>

1. 4本。一覧で1本、記事ごとのタグで1本ずつ（検証済み）。2-4 で減らす
2. 保証されない。テストでは逆順で返った（並び順の決め方は 2-12）

</details>

### 3-7. ✅ 想起チェック

1. `ManyToManyField` を足したとき、`blog_post` に列は増える？

<details><summary>答え</summary>

1. 増えない。つなぎの台帳ができる

</details>

### 3-8. 📇 まとめカード

この回で覚えることは1つだけ: **多対多は、つなぎの台帳に「記事とタグの組」を並べてつなぐ。**

📒 用語集に追記: 多対多 / つなぎの台帳

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第2部 ステップ4` — N+1 問題を見て直す

---

## 第2部-4: N+1 問題を見て直す

**❓ この回の問い**: 2-3 で、記事3件の一覧に SQL が4本出た。1000件なら何本？

**作るもの**: 記事が何件でも、一覧の SQL を2本にする
**重要度**: 🔴 毎日使う — 一覧 API を書くたびに確かめる
**前ステップとの接続**: 2-3 の一覧にカテゴリも足してから直す

### 4-0. このステップの初出

**Django / Ninja**: `select_related`, `prefetch_related` / **Python**: なし

> 🧒 **かみくだくと**: **N+1 問題**は、一覧の SQL 1本のあとに、1件ごとに関連データを取りに行くこと。
> SQL が「1 + 件数」本になる。

### 4-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

**① カテゴリも入れ子で返す**（`blog/api.py` の差分）

```python
class CategoryOut(Schema):
    id: int
    name: str


class PostOut(Schema):
    # （既存の項目はそのまま）
    category: CategoryOut | None  # 入れ子: カテゴリの名前も返す
```

記事3件（カテゴリ・タグ付き）の一覧で、SQL が7本出ます。

```sql
SELECT ... FROM `blog_post`
SELECT ... FROM `blog_category` WHERE `blog_category`.`id` = 1 LIMIT 21
SELECT ... FROM `blog_tag` INNER JOIN `blog_post_tags` ... WHERE `blog_post_tags`.`post_id` = 1
SELECT ... FROM `blog_category` WHERE `blog_category`.`id` = 2 LIMIT 21
SELECT ... FROM `blog_tag` INNER JOIN `blog_post_tags` ... WHERE `blog_post_tags`.`post_id` = 2
SELECT ... FROM `blog_category` WHERE `blog_category`.`id` = 1 LIMIT 21
SELECT ... FROM `blog_tag` INNER JOIN `blog_post_tags` ... WHERE `blog_post_tags`.`post_id` = 3
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / django-ninja 1.7.1 / MySQL 8.4.11（列名は `...` で省略。同じカテゴリ `id = 1` も2回取っている）

**② 直す**（`blog/api.py` の `list_posts`）

```python
@router.get("", response=list[PostOut])
def list_posts(request: HttpRequest):
    return (
        Post.objects.select_related("category")  # カテゴリは JOIN で同じ SQL に入れる
        .prefetch_related("tags")  # タグは別の SQL 1本でまとめて取る
        .all()
    )
```

```sql
SELECT `blog_post`.`id`, ..., `blog_category`.`id`, `blog_category`.`name` FROM `blog_post` LEFT OUTER JOIN `blog_category` ON (`blog_post`.`category_id` = `blog_category`.`id`)
SELECT (`blog_post_tags`.`post_id`) AS `_prefetch_related_val_post_id`, `blog_tag`.`id`, `blog_tag`.`name` FROM `blog_tag` INNER JOIN `blog_post_tags` ON (`blog_tag`.`id` = `blog_post_tags`.`tag_id`) WHERE `blog_post_tags`.`post_id` IN (1, 2, 3)
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / django-ninja 1.7.1 / MySQL 8.4.11（記事10件でも2本。応答の中身は直す前と同じ）

**③ 本数をテストで固定する**（`tests/test_query_count.py` 新規・全文）

```python
import pytest
from ninja.testing import TestClient

from blog.models import Category, Post, Tag
from config.api import api

client = TestClient(api)


@pytest.mark.django_db
@pytest.mark.parametrize("n_posts", [3, 10])  # 記事3件と10件で、同じテストを2回流す
def test_list_posts_query_count_does_not_grow(n_posts: int, django_assert_num_queries) -> None:
    category = Category.objects.create(name="日記")
    tags = [Tag.objects.create(name="python"), Tag.objects.create(name="django")]
    for i in range(n_posts):
        post = Post.objects.create(title=f"記事{i}", body="b", category=category)
        post.tags.set(tags)

    # この中で出た SQL がちょうど2本でなければ失敗する
    with django_assert_num_queries(2):
        res = client.get("/posts")

    assert res.status_code == 200
    assert len(res.json()) == n_posts
```

✅ 検証済み: pytest-django 4.14.0（`11 passed`。ruff・mypy も通過）

`django_assert_num_queries` は pytest-django の道具です。引数に名前を書くと pytest が渡します。`parametrize` は、値を変えて同じテストを流す指定です。

### 4-2. 🔬 仕組み解剖

| | `select_related` | `prefetch_related` |
| --- | --- | --- |
| 正式名称 | QuerySet の `select_related()` | QuerySet の `prefetch_related()` |
| いつ・誰が | 一覧の SQL に JOIN を足す | `IN (…)` の SQL を1本足し、Python でつなぐ |
| TS での対応物 | 対応物なし | DataLoader の「まとめて取る」に近い |
| なぜこの設計 | 相手が1つなら JOIN で行が増えない | 相手が複数だと行が増えるので分ける |
| 失敗すると | 多対多に使うと `FieldError`（検証済み） | 付け忘れると N+1 に戻る |

```text
直す前: 1 + 3 + 3 = 7本 … 記事が増えると増える
直した後:
  ① SELECT 記事 LEFT OUTER JOIN カテゴリ      … 1本
  ② SELECT タグ WHERE post_id IN (1, 2, 3)    … 1本
  合計 2本 … 記事が何件でも変わらない
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / MySQL 8.4.11

見てほしいのは、**本数が件数に比例しなくなった**点。

### 4-3. 🐍 Python注

（この回は新しい文法なし）

### 4-4. 解説 — なぜこう設計するか

`QuerySet` は使うまで SQL を出しません（1-5）。だから「何を一緒に取るか」を前もって足せます。

🧠 Django の考え方: 取り方の指示は QuerySet に足すだけ。

### 4-5. 🏢 実務メモ

> 🏢 **実務メモ**: 多対一は `select_related`、多対多は `prefetch_related`。
> 根拠: https://docs.djangoproject.com/en/5.2/ref/models/querysets/#prefetch-related

### 4-6. 🔮 予測 → 動作確認

1. 直す前のコードで、記事10件なら SQL は何本？
2. 直す前のコードで ③ のテストを流すと？（試したら戻す）

<details><summary>答え</summary>

1. 21本（1 + カテゴリ10 + タグ10。7本の内訳からの計算）
2. 失敗する。`Failed: Expected to perform 2 queries but 7 were done`（記事3件の回。検証済み）

</details>

### 4-7. ✅ 想起チェック

1. カテゴリは `select_related`、タグは `prefetch_related`。分けたのはなぜ？

<details><summary>答え</summary>

1. カテゴリは1件に1つで JOIN で済む。タグは複数で、JOIN すると行が増える

</details>

### 4-8. 📇 まとめカード

この回で覚えることは1つだけ: **一覧は、関連データを `select_related` / `prefetch_related` でまとめて取る。**

📒 用語集に追記: N+1 問題 / JOIN

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第2部 ステップ5` — ミドルウェア
