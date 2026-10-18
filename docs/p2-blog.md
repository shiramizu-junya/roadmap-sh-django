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

---

## 第2部-5: ミドルウェア

**❓ この回の問い**: 2-4 で SQL は2本になった。では、1回のリクエストに何ミリ秒かかっている？

**作るもの**: 全リクエストの所要時間を、runserver のコンソールに1行で出す
**重要度**: 🟡 読めればよい — 自作は少ないが、`MIDDLEWARE` の並びはよく読む
**前ステップとの接続**: `settings.py` の `MIDDLEWARE` と `LOGGING` に1つずつ足す

### 5-0. このステップの初出

**Django / Ninja**: `MIDDLEWARE`（自作）, `LOGGING` / **Python**: 関数の中の関数, `__name__`

> 🧒 **かみくだくと**: **ミドルウェア**は、窓口の順路に置かれた共通の検査。
> 全リクエストが、行きと帰りに必ず通る。
> **ロガー**は、名前付きのログの出し口。何を画面に出すかは `LOGGING` で決める。

### 5-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

**① ミドルウェアを書く**（`config/middleware.py` 新規・全文）

```python
import logging
import time

# ログの出し口。名前は "config.middleware"（このファイルの場所）になる
logger = logging.getLogger(__name__)


def timing_middleware(get_response):
    # ここはサーバ起動時に1回だけ動く。get_response は「次の層」
    def middleware(request):
        # ここから下は、リクエストのたびに動く
        start = time.perf_counter()
        response = get_response(request)  # 次の層へ渡す。戻ってくるとレスポンスがある
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %s (%.1f ms)",
            request.method,
            request.path,
            response.status_code,
            elapsed_ms,
        )
        return response

    return middleware
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17（ruff・mypy も通過）

**② 順路に置く**（`config/settings.py` の `MIDDLEWARE`。先頭に1行足す差分）

```python
MIDDLEWARE = [
    "config.middleware.timing_middleware",  # 追加: 一番外側で全体の時間を測る
    "django.middleware.security.SecurityMiddleware",
    # （残りはそのまま）
]
```

ここで叩いても、**計測の行はまだ出ません**（理由は 5-2）。

✅ 検証済み: 200 は返るが、コンソールには SQL と `"GET /api/posts HTTP/1.1" 200 754` しか出ない

**③ ロガーを出す設定**（`config/settings.py` の `LOGGING` に足す差分）

```python
LOGGING = {
    # （"version" / "handlers" / "django.db.backends" はそのまま）
    "loggers": {
        "django.db.backends": {...},  # 既存の SQL ログ
        # 追加: 自作ミドルウェアのログ。INFO 以上をコンソールに出す
        "config.middleware": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
```

```bash
SQL_LOG=0 uv run python manage.py runserver
# 別のターミナルで
curl -s -o /dev/null http://127.0.0.1:8000/api/posts
curl -s -o /dev/null http://127.0.0.1:8000/api/posts/999
curl -s -o /dev/null http://127.0.0.1:8000/nothing
```

```text
GET /api/posts -> 200 (36.8 ms)
[13/Oct/2026 13:12:44] "GET /api/posts HTTP/1.1" 200 754
GET /api/posts/999 -> 404 (16.0 ms)
Not Found: /api/posts/999
[13/Oct/2026 13:12:44] "GET /api/posts/999 HTTP/1.1" 404 57
GET /nothing -> 404 (2.5 ms)
Not Found: /nothing
[13/Oct/2026 13:12:44] "GET /nothing HTTP/1.1" 404 2499
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / MySQL 8.4.11（ミリ秒は毎回変わる。`SQL_LOG=0` を外すと、SQL の行のすぐ後に計測の行が出る）

### 5-2. 🔬 仕組み解剖

| | `MIDDLEWARE`（自作） | `LOGGING` |
| --- | --- | --- |
| 正式名称 | middleware（関数で書く形） | logging configuration |
| いつ・誰が | 起動時に Django が外側の関数を1回呼ぶ。中の関数はリクエストごと | 起動時に Django が読み、Python の `logging` に渡す |
| TS での対応物 | Koa の `await next()` の前後に書くのと同じ形 | 対応物なし。`console.log` には出す・出さないの設定が無い |
| なぜこの設計 | ビュー全部に計測を書かず、1か所で済む | 出す側（`logger.info`）と見せる側（`LOGGING`）を分ける |
| 失敗すると | 名前の綴りを誤ると起動時に `ImportError`。`return response` を忘れると 500 | 設定が無いと `INFO` は黙って捨てられる（②で見た） |

```text
リクエスト
  ↓ timing_middleware       start を記録
  ↓ SecurityMiddleware
  ↓ ……（残り6つ）
  ↓ URL ルーティング → ビュー関数（list_posts）
  ↑ ……（同じ順路を逆向きに戻る）
  ↑ SecurityMiddleware
  ↑ timing_middleware       経過時間をログに出す
レスポンス
```

✅ 検証済み: Django 5.2.17（`/nothing` も計測された。URL ルーティングより手前で動くため）

見てほしいのは、**行きは上から、帰りは下から**通る点です。

②で出なかったのは、既定では `WARNING` 以上しか表示されないからです。

### 5-3. 🐍 Python注

> 🐍 **Python注**: `def` の中の `def` は、関数を作って返す書き方。中の関数は外の `get_response` を覚えている（TS のクロージャ）。
> `__name__` は、今のファイルの名前（`"config.middleware"`）が入る変数。

### 5-4. 解説 — なぜこう設計するか

共通の処理をビューごとに書くと、書き忘れが出ます。CSRF の検査なども、既存のミドルウェアです。

🧠 Django の考え方: 全員に共通の処理は、窓口の順路に置く。

### 5-5. 🏢 実務メモ

> 🏢 **実務メモ**: ミドルウェアは並び順に意味がある。計測は全体を包みたいので先頭に置く。
> 根拠: https://docs.djangoproject.com/en/5.2/topics/http/middleware/#middleware-order-and-layering

### 5-6. 🔮 予測 → 動作確認

1. 存在しない URL `/nothing` でも、計測の行は出る？
2. `uv run pytest -s` で、計測の行は出る？

<details><summary>答え</summary>

1. 出る（`404`）。ミドルウェアは URL ルーティングより手前で動く
2. 出ない。`TestClient` はミドルウェアを通らない（1-12。検証済み）

</details>

### 5-7. ✅ 想起チェック

1. `get_response(request)` より前の行と後の行は、それぞれいつ動く？
2. 外側の `timing_middleware` 自体は、何回呼ばれる？

<details><summary>答え</summary>

1. 前はビューより先（行き）。後はレスポンスができたあと（帰り）
2. 起動時に1回だけ。リクエストごとに動くのは中の `middleware`

</details>

### 5-8. 📇 まとめカード

この回で覚えることは1つだけ: **共通の処理は `get_response` の前後に書き、`MIDDLEWARE` に並べる。**

📒 用語集に追記: ミドルウェア / ロガー / ログレベル

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第2部 ステップ6` — JWT でログイン

---

## 第2部-6: JWT でログイン

**❓ この回の問い**: 2-5 で全リクエストを見張れた。では、リクエストが「誰から」来たかはどう分かる？

**作るもの**: ユーザー名とパスワードで、JWT（身分証）を返すログイン API
**重要度**: 🔴 毎日使う — API のログインは、ほぼこの形
**前ステップとの接続**: `accounts/api.py` を作り、2-1 と同じく差し込む

### 6-0. このステップの初出

**Django / Ninja**: `authenticate()`, `RefreshToken`（django-ninja-jwt） / **Python**: `try` / `except`

> 🧒 **かみくだくと**: **JWT**（JSON Web Token）は、`user_id` とサーバの署名が付いた**身分証**。署名を確かめれば、台帳を見ずに本物と分かる。
> **アクセストークン**は身分証そのもの（5分）。**リフレッシュトークン**は新しい身分証との**引換券**（1日）。

### 6-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

**① ライブラリを入れる**

```bash
uv add django-ninja-jwt
```

✅ 検証済み: django-ninja-jwt 5.4.5（依存として django-ninja-extra 0.31.7 と PyJWT 2.15.1 も入る。`INSTALLED_APPS` への追加は不要）

**② ログイン API**（`accounts/api.py` 新規・全文）

```python
from django.contrib.auth import authenticate
from django.http import HttpRequest
from ninja import Router, Schema, Status
from ninja_jwt.exceptions import TokenError
from ninja_jwt.tokens import RefreshToken

# ログインまわりの API 一式。URL の頭（/auth）は config/api.py で決める
router = Router()


class LoginIn(Schema):
    username: str
    password: str


class TokenOut(Schema):
    access: str  # 身分証。API を呼ぶたびに見せる（有効期限が短い）
    refresh: str  # 身分証の引換券。access が切れたら新しいものと交換する


class RefreshIn(Schema):
    refresh: str


class AccessOut(Schema):
    access: str


class ErrorOut(Schema):
    detail: str


@router.post("/login", response={200: TokenOut, 401: ErrorOut})
def login(request: HttpRequest, payload: LoginIn):
    # ユーザー名とパスワードが合えば User、合わなければ None が返る
    user = authenticate(request, username=payload.username, password=payload.password)
    if user is None:
        return Status(401, {"detail": "ユーザー名かパスワードが違います"})
    # 引換券を作る（中に user_id が入る）
    # ignore: ライブラリの型注釈の誤り（cls: T）で mypy が怒るのを黙らせる。動きは正しい
    refresh = RefreshToken.for_user(user)  # type: ignore[misc]
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


@router.post("/refresh", response={200: AccessOut, 401: ErrorOut})
def refresh(request: HttpRequest, payload: RefreshIn):
    try:
        token = RefreshToken(payload.refresh)  # 署名と有効期限をここで確かめる
    except TokenError:
        return Status(401, {"detail": "引換券が無効か、期限切れです"})
    return {"access": str(token.access_token)}
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / django-ninja 1.7.1 / django-ninja-jwt 5.4.5（ruff・mypy も通過）

**③ 差し込む**（`config/api.py` の差分）

```python
from accounts.api import router as auth_router  # 追加
from blog.api import router as posts_router

# （api = NinjaAPI() と posts の add_router はそのまま）
api.add_router("/auth", auth_router, tags=["auth"])  # 追加
```

✅ 検証済み: Swagger UI（`/api/docs`）に `auth` の2本が増える

**④ ログインして、身分証を読む**（名前とパスワードは自分の管理者ユーザーに置き換える）

```bash
curl -s -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "pass1234"}' | uv run python -m json.tool
```

```text
{
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNz...EkcpWrr-26YVjraQIBovh5TdeXwLphTflFYkTsjPUyY",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVz...K_l_U-h1DF_zWMmCsNmC47AvgPTrCVhHDFbt0JuChQY"
}
```

✅ 検証済み: MySQL 8.4.11（長いので途中を `...` で省略。値は毎回変わる）

`.` で区切った真ん中が中身です。暗号化されておらず、だれでも読めます。
access の値を変数 `ACCESS` に入れてから読みます（2-7 でもこの変数を使います）。

```bash
# ログインして、access の値だけを変数 ACCESS に入れる
ACCESS=$(curl -s -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "pass1234"}' \
  | uv run python -c "import json, sys; print(json.load(sys.stdin)['access'])")

# 真ん中（中身）を取り出して読む
uv run python -c "import base64, json, sys; body = sys.argv[1].split('.')[1]; print(json.loads(base64.urlsafe_b64decode(body + '==')))" "$ACCESS"
```

```text
{'token_type': 'access', 'exp': 1791898367, 'iat': 1791898067, 'jti': '92082b76ab4e40759c8cc83775b9ff00', 'user_id': 1}
```

✅ 検証済み: `exp`（期限）−`iat`（発行時刻）＝300秒＝5分。refresh 側は 86400秒＝1日

**⑤ テスト**（`tests/test_auth.py` 新規・全文。`# TODO` の下は先に自分で書く）

```python
import pytest
from ninja.testing import TestClient

from accounts.models import User
from config.api import api

client = TestClient(api)


@pytest.mark.django_db
def test_login_returns_tokens() -> None:
    User.objects.create_user(username="alice", password="pass1234")
    res = client.post("/auth/login", json={"username": "alice", "password": "pass1234"})
    # TODO: 200 で、access と refresh の両方が返ること
    assert res.status_code == 200
    assert set(res.json()) == {"access", "refresh"}


@pytest.mark.django_db
def test_wrong_password_is_401() -> None:
    User.objects.create_user(username="alice", password="pass1234")
    res = client.post("/auth/login", json={"username": "alice", "password": "wrong"})
    # TODO: 401 で、トークンを返さないこと
    assert res.status_code == 401
    assert "access" not in res.json()


@pytest.mark.django_db
def test_refresh_gives_new_access() -> None:
    User.objects.create_user(username="alice", password="pass1234")
    tokens = client.post("/auth/login", json={"username": "alice", "password": "pass1234"}).json()
    # TODO: refresh を渡すと 200。access を渡すと 401（種類が違う）
    assert client.post("/auth/refresh", json={"refresh": tokens["refresh"]}).status_code == 200
    assert client.post("/auth/refresh", json={"refresh": tokens["access"]}).status_code == 401
```

✅ 検証済み: pytest-django 4.14.0（`14 passed`。ruff・mypy も通過）

### 6-2. 🔬 仕組み解剖

| | `authenticate()` | `RefreshToken` |
| --- | --- | --- |
| 正式名称 | `django.contrib.auth.authenticate()` | `ninja_jwt.tokens.RefreshToken` |
| いつ・誰が | リクエストごと。Django がユーザー名で User を引き、パスワードのハッシュを照合する | `for_user()` で作り、`SECRET_KEY` で署名する。`RefreshToken(文字列)` で署名と期限を確かめる |
| 発行される SQL | `SELECT ... FROM accounts_user WHERE username = 'alice' LIMIT 21` の1本 | **0本**。台帳を見ない |
| TS での対応物 | 対応物なし。Node では bcrypt などで照合を自分で組む | jsonwebtoken の `jwt.sign()` / `jwt.verify()` |
| なぜこの設計 | パスワード照合を各自で書かせない | サーバが「誰がログイン中か」を覚えなくて済む |
| 失敗すると | 例外ではなく `None` が返る。401 は自分で返す | 改ざん・期限切れ・種類違いで `TokenError`（④の後で確認。3つとも 401） |

✅ 検証済み: Django 5.2.17 / django-ninja-jwt 5.4.5（SQL の本数は `CaptureQueriesContext` で数えた）

```text
① POST /api/auth/login    {username, password}
     → authenticate() で照合（SQL 1本）
     ← {access, refresh}
② API を呼ぶたびに access を見せる   … 2-7 で使う
③ access が切れたら（5分）
   POST /api/auth/refresh  {refresh}
     ← {access}（新しい身分証。SQL 0本）
④ refresh も切れたら（1日） → ① からやり直す
```

見てほしいのは、**台帳を見るのは①だけ**という点です。

**セッション認証との比較**（1-4 の回収）。管理画面は今もセッション認証で動いています。

| | セッション認証（管理画面） | JWT（この API） |
| --- | --- | --- |
| サーバが状態を持つか | 持つ。`django_session` に1行増える | 持たない。行は増えない |
| どこで運ぶか | Cookie（`sessionid`） | ヘッダ（`Authorization: Bearer ...`） |
| 即時ログアウト | できる（行を消す） | できない。期限まで有効 |
| CSRF 対策 | 要る。ブラウザが Cookie を自動で送るため | 要らない。ヘッダは自動で付かないため |

✅ 検証済み: ログイン API の後は `django_session` が0件のまま。管理画面にログインすると1件になり、`sessionid` の Cookie が届いた

### 6-3. 🐍 Python注

> 🐍 **Python注**: `try:` / `except TokenError:` は TS の `try` / `catch`。捕まえる例外を種類で選ぶ。
> `set(...)` は、順番を無視して中身だけ比べるため。

### 6-4. 解説 — なぜこう設計するか

JWT ならサーバを何台に増やしても、同じ身分証が通ります。そのかわり、配った身分証は取り消せません。だから期限を短くして、引換券で交換させます。

🧠 Django の考え方: 照合は Django、身分証はライブラリに任せる。

### 6-5. 🔓 教材用の簡略化

> 🔓 **教材用の簡略化**: 期限は既定のまま（access 5分 / refresh 1日）。引換券は何度でも使える。
> **本番では**: 使った引換券を無効にする（`ROTATE_REFRESH_TOKENS` など）。署名の鍵も `SIGNING_KEY` で分ける。
> 根拠: https://eadwincode.github.io/django-ninja-jwt/settings/

### 6-6. 🔮 予測 → 動作確認

1. runserver のログ（2-5）で、`/login` と `/refresh` はどちらが遅い？

<details><summary>答え</summary>

1. `/login`。検証では 692.7 ms と 0.4 ms。パスワードのハッシュ照合は、総当たりを防ぐためにわざと遅い（根拠: https://docs.djangoproject.com/en/5.2/topics/auth/passwords/）

</details>

### 6-7. ✅ 想起チェック

1. JWT のログインで、サーバの台帳に増える行は？
2. パスワードが違うと、`authenticate()` は何を返す？

<details><summary>答え</summary>

1. 無い（セッション認証なら `django_session` に1行）
2. `None`。401 は自分で返す

</details>

### 6-8. 📇 まとめカード

この回で覚えることは1つだけ: **`authenticate()` で照合し、合えば `RefreshToken.for_user()` で身分証を渡す。**

📒 用語集に追記: JWT / アクセストークン / リフレッシュトークン / セッション認証

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第2部 ステップ7` — 認証と権限

---

## 第2部-7: 認証と権限

**❓ この回の問い**: 2-6 で身分証を発行できた。では、記事の API で身分証を確かめるには？

**作るもの**: 作成は要ログイン（401）。更新・削除は自分の記事だけ（403）
**重要度**: 🔴 毎日使う — 書き込む API には、ほぼ必ず付ける
**前ステップとの接続**: 2-6 の access を、記事の API で確かめる

### 7-0. このステップの初出

**Django / Ninja**: `JWTAuth`（`auth=`）, `HttpError` / **Python**: `raise`, `@pytest.fixture`

> 🧒 **かみくだくと**: **認証**は「誰か」を身分証で確かめること。失敗は **401**。
> **認可**（権限）は「その人がしてよいか」を決めること。失敗は **403**。

### 7-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

**① 記事に「書いた人」を足す**（`blog/models.py` の差分）

```python
from django.conf import settings  # 追加（ファイルの先頭）
from django.db import models


class Post(models.Model):
    # （既存の項目はそのまま。tags の下に追加）
    # 多対一: 記事を書いた人。ユーザーを消すと、その人の記事も消える
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # accounts.User を指す（1-2 の設定）
        on_delete=models.CASCADE,
        null=True,  # 既存の記事には書いた人がいないので、空を許す
        blank=True,
    )
```

```bash
uv run python manage.py makemigrations blog
SQL_LOG=0 uv run python manage.py sqlmigrate blog 0004
uv run python manage.py migrate
```

```sql
ALTER TABLE `blog_post` ADD COLUMN `author_id` bigint NULL , ADD CONSTRAINT `blog_post_author_id_dd7a8485_fk_accounts_user_id` FOREIGN KEY (`author_id`) REFERENCES `accounts_user`(`id`);
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / MySQL 8.4.11（制約名の末尾は環境で変わる）

**② 記事の API に身分証の確認を付ける**（`blog/api.py` の差分）

```python
from ninja.errors import HttpError  # 追加
from ninja_jwt.authentication import JWTAuth  # 追加


class PostOut(Schema):
    # （既存の項目はそのまま。category_id の下に追加）
    author_id: int | None  # 書いた人の id（既存の記事は null）


@router.post("", response={201: PostOut}, auth=JWTAuth())  # 身分証が無ければ 401
def create_post(request: HttpRequest, payload: PostIn):
    category = None
    if payload.category_id is not None:
        category = get_object_or_404(Category, id=payload.category_id)
    # 無いタグが1つでもあれば 404（記事を作る前に確かめる）
    tags = [get_object_or_404(Tag, id=tag_id) for tag_id in payload.tag_ids]
    post = Post.objects.create(
        title=payload.title,
        body=payload.body,
        category=category,
        # 身分証の持ち主を、書いた人にする。author=request.user だと mypy が型違いを指摘する
        author_id=request.user.id,
    )
    post.tags.set(tags)
    return Status(201, post)


@router.patch("/{post_id}", response=PostOut, auth=JWTAuth())
def update_post(request: HttpRequest, post_id: int, payload: PostPatch):
    post = get_object_or_404(Post, id=post_id)
    if post.author_id != request.user.id:
        raise HttpError(403, "自分の記事しか変更できません")
    # （以下はそのまま）


@router.delete("/{post_id}", response={204: None}, auth=JWTAuth())
def delete_post(request: HttpRequest, post_id: int):
    post = get_object_or_404(Post, id=post_id)
    if post.author_id != request.user.id:
        raise HttpError(403, "自分の記事しか削除できません")
    # （以下はそのまま）
```

✅ 検証済み: django-ninja 1.7.1 / django-ninja-jwt 5.4.5（ruff・mypy も通過）

**③ 叩いてみる**（`ACCESS` は 2-6 ④の方法で入れておく）

```bash
# 身分証なし → 401
curl -s -X POST http://127.0.0.1:8000/api/posts -H "Content-Type: application/json" -d '{"title": "t", "body": "b"}'
# 身分証あり → 201。author_id が自分の id になる
curl -s -X POST http://127.0.0.1:8000/api/posts -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" -d '{"title": "自分の記事", "body": "b"}'
# 書いた人のいない既存の記事（id は自分の環境のもの）→ 403
curl -s -X PATCH http://127.0.0.1:8000/api/posts/2 -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" -d '{"title": "x"}'
```

```text
{"detail": "Unauthorized"}
{"id": 4, "title": "自分の記事", "body": "b", ..., "author_id": 1, "tags": [], "category": null}
{"detail": "自分の記事しか変更できません"}
```

✅ 検証済み: 401 / 201 / 403（日本語は `自...` の形で返る。1-5 と同じ）。`GET /api/posts` は身分証なしで 200 のまま

```bash
# 書いた人のいない既存の記事に、自分を入れる（任意。1回だけ。ユーザー名は自分のものに）
uv run python manage.py shell -c "from accounts.models import User; from blog.models import Post; print(Post.objects.filter(author=None).update(author=User.objects.get(username='alice')))"
```

```sql
UPDATE `blog_post` SET `author_id` = 1 WHERE `blog_post`.`author_id` IS NULL
```

✅ 検証済み: 最後に更新した行数が出る

**④ テストに身分証を持たせる**（`tests/conftest.py` 新規・全文）

```python
import pytest
from ninja_jwt.tokens import RefreshToken

from accounts.models import User


@pytest.fixture
def user(db) -> User:
    # ログインしている人。引数に user と書いたテストに渡される
    return User.objects.create_user(username="alice", password="pass1234")


@pytest.fixture
def auth_headers(user: User) -> dict[str, str]:
    # user の身分証を、リクエストのヘッダの形にする
    token = RefreshToken.for_user(user).access_token  # type: ignore[misc]
    return {"Authorization": f"Bearer {token}"}
```

✅ 検証済み: pytest-django 4.14.0

> 💡補足: プロジェクト直下にも `conftest.py` があると、mypy が `Duplicate module named "conftest"` で止まる。空の `tests/__init__.py` を作れば、`tests.conftest` という別の名前として区別される。

**⑤ 既存のテストを直す**

②のあと、既存のテストが 401 / 403 で落ちます。引数に `auth_headers`（記事を作るなら `user` も）を足し、`headers=` と `author=` を渡して直します。

<details><summary>解答例（test_posts_api.py の差分。test_categories.py・test_tags.py も同じ形）</summary>

```diff
# 長すぎる行は uv run ruff format tests で折り返す
+from accounts.models import User
 from blog.models import Post

-def test_create_and_get_post() -> None:
-    res = client.post("/posts", json={"title": "テスト", "body": "本文"})
+def test_create_and_get_post(auth_headers: dict[str, str]) -> None:
+    res = client.post("/posts", json={"title": "テスト", "body": "本文"}, headers=auth_headers)

-def test_update_changes_only_sent_fields() -> None:
-    post = Post.objects.create(title="元の題名", body="元の本文")
-    res = client.patch(f"/posts/{post.id}", json={"title": "新しい題名"})
+def test_update_changes_only_sent_fields(user: User, auth_headers: dict[str, str]) -> None:
+    post = Post.objects.create(title="元の題名", body="元の本文", author=user)
+    res = client.patch(f"/posts/{post.id}", json={"title": "新しい題名"}, headers=auth_headers)
```

</details>

✅ 検証済み: 直したあと `ruff format` を通して全件成功

**⑥ 権限のテスト**（`tests/test_permissions.py` 新規・全文）

```python
import pytest
from ninja.testing import TestClient

from accounts.models import User
from blog.models import Post
from config.api import api

client = TestClient(api)


@pytest.mark.django_db
def test_create_without_token_is_401() -> None:
    res = client.post("/posts", json={"title": "t", "body": "b"})
    # TODO: 401 で、記事が保存されていないこと
    assert res.status_code == 401
    assert Post.objects.count() == 0


def test_create_sets_author(user: User, auth_headers: dict[str, str]) -> None:
    res = client.post("/posts", json={"title": "t", "body": "b"}, headers=auth_headers)
    # TODO: 応答の author_id が、ログインしている人の id であること
    assert res.json()["author_id"] == user.id


def test_cannot_change_others_post(auth_headers: dict[str, str]) -> None:
    bob = User.objects.create_user(username="bob", password="pass1234")
    post = Post.objects.create(title="bob の記事", body="b", author=bob)
    # TODO: alice（auth_headers）が bob の記事を変更・削除すると 403。記事はそのまま
    res = client.patch(f"/posts/{post.id}", json={"title": "乗っ取り"}, headers=auth_headers)
    assert res.status_code == 403
    assert client.delete(f"/posts/{post.id}", headers=auth_headers).status_code == 403
    assert Post.objects.get(id=post.id).title == "bob の記事"
```

✅ 検証済み: pytest-django 4.14.0（`17 passed`。ruff・mypy も通過）

### 7-2. 🔬 仕組み解剖

| | `JWTAuth`（`auth=`） | `HttpError` |
| --- | --- | --- |
| 正式名称 | Ninja の認証（`auth=`）に渡す、django-ninja-jwt の Bearer 認証クラス | `ninja.errors.HttpError` |
| いつ・誰が | リクエストごと。**ビュー関数より前に** Ninja が呼ぶ。署名と期限を確かめ、User を引いて `request.user` に入れる | ビュー関数の中で `raise` した時点で処理を止める。Ninja が受け止めて応答を作る |
| 発行される SQL | `SELECT ... FROM accounts_user WHERE id = 1 LIMIT 21` の1本（その人がまだ有効か確かめる） | なし |
| TS での対応物 | Express で、ルートごとに認証ミドルウェアを挟む `app.post("/posts", requireAuth, handler)` | `throw new HttpError(403, ...)` を共通のエラーハンドラが受ける形 |
| なぜこの設計 | 「誰か」の確認をビューから外し、宣言1つで付け外しできる | 失敗の応答の形（`{"detail": ...}`）をそろえる |
| 失敗すると | ヘッダが無いと 401 `{"detail": "Unauthorized"}`。偽物・期限切れも 401 | 指定したコードと `{"detail": "<メッセージ>"}` |

✅ 検証済み: Django 5.2.17 / django-ninja 1.7.1 / django-ninja-jwt 5.4.5

```text
PATCH /api/posts/1  （Authorization: Bearer <access>）
  ↓ ミドルウェア（2-5）
  ↓ URL ルーティング
  ↓ auth=JWTAuth()   身分証が無い・偽物 ────→ 401（ビューは動かない）
  ↓                  本物なら User を引く（SQL 1本）
  ↓ update_post
  ↓   記事が無い ─────────────────────→ 404
  ↓   書いた人が違う（raise HttpError）─→ 403
  ↓   本人
  200
```

✅ 検証済み: 3つの分かれ道すべて（無い id 999 は、身分証ありで 404）

見てほしいのは、**401 はビューの手前、403 はビューの中**で決まる点です。

> 💡補足: 偽物の身分証の 401 は、`detail` が崩れた文字列になる（ライブラリの都合。401 自体は正しい）。

### 7-3. 🐍 Python注

> 🐍 **Python注**: `raise` は例外を投げて、その場で処理を止める（TS の `throw`）。
> `@pytest.fixture` を付けた関数は、テストの引数に同じ名前を書くと、pytest が呼んで結果を渡す。

### 7-4. 解説 — なぜこう設計するか

認可をビューで書くのは、「誰の記事か」がデータを見ないと分からないからです。

🧠 Django の考え方: 「誰か」は入口で、「してよいか」はデータを見てから。

### 7-5. 🏢 実務メモ

> 🏢 **実務メモ**: `auth=` は Router にも付けられ、配下の全 API に効く。外すには `auth=None`。
> 根拠: https://django-ninja.dev/guide/authentication/#applying-auth-at-different-levels

### 7-6. 🔮 予測 → 動作確認

1. 身分証ありで、存在しない記事 `999` を PATCH すると？
2. 他人の記事を PATCH して 403 になるまでに、SQL は何本？

<details><summary>答え</summary>

1. 404。所有者を確かめる前に `get_object_or_404` で止まる（検証済み）
2. 2本。User と記事を1本ずつ（ログで確認済み）

</details>

### 7-7. ✅ 想起チェック

1. 401 と 403 の違いは？
2. `auth=JWTAuth()` が失敗したとき、ビュー関数は動く？

<details><summary>答え</summary>

1. 401 は誰か分からない。403 は誰かは分かったが許可がない
2. 動かない。Ninja がビューの手前で 401 を返す

</details>

### 7-8. 📇 まとめカード

この回で覚えることは1つだけ: **認証は `auth=` で入口に、認可はビューでデータを見て `HttpError(403)`。**

📒 用語集に追記: 認証 / 認可 / 401 と 403 / フィクスチャ

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第2部 ステップ8` — ユーザー登録とプロフィール（一対一）

---

## 第2部-8: ユーザー登録とプロフィール（一対一）

**❓ この回の問い**: 2-7 で「ログインした人だけ」書き込めるようになった。では、そのユーザーはどうやって増やす？

**作るもの**: 登録 API（`POST /api/auth/register`）と、自分のプロフィールを読み書きする API（`/api/auth/me`）
**重要度**: 🔴 毎日使う — ユーザー登録と「User に情報を足す」設計は、ほぼどのアプリにも出る
**前ステップとの接続**: 2-6 のログインの前に「登録」を足し、User に Profile を一対一でつなぐ

### 8-0. このステップの初出

**Django / Ninja**: `create_user()`, `OneToOneField` / **Python**: なし

> 🧒 **かみくだくと**: **一対一**は「1人に、1つだけ」のつながり。
> 住民台帳（User）とは別に、自己紹介の台帳（Profile）を作り、1人につき1行だけ書けるようにする。

### 8-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

**① Profile を作る**（`accounts/models.py` 全文）

```python
# Create your models here.
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    # 今は AbstractUser の項目をそのまま使う。項目を足すときはここに書く
    pass


class Profile(models.Model):
    # 一対一: 1人のユーザーに、プロフィールは1つだけ
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)  # 自己紹介。空でもよい

    def __str__(self) -> str:
        return f"{self.user_id} のプロフィール"
```

```bash
uv run python manage.py makemigrations accounts
SQL_LOG=0 uv run python manage.py sqlmigrate accounts 0002
uv run python manage.py migrate
```

```sql
CREATE TABLE `accounts_profile` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `bio` longtext NOT NULL, `user_id` bigint NOT NULL UNIQUE);
ALTER TABLE `accounts_profile` ADD CONSTRAINT `accounts_profile_user_id_49a85d32_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`);
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / MySQL 8.4.11（制約名の末尾は環境で変わる）

2-2 の `ForeignKey` との違いは、`user_id` の **`UNIQUE` だけ**です。

**② 登録とプロフィールの API**（`accounts/api.py`。先頭の import を置き換え、ファイルの最後に追加。既存の login と refresh は消さない）

先頭の import（この形に置き換える）

```python
from django.contrib.auth import authenticate
from django.http import HttpRequest
from django.shortcuts import get_object_or_404  # 追加
from ninja import Field, Router, Schema, Status  # Field を追加
from ninja_jwt.authentication import JWTAuth  # 追加
from ninja_jwt.exceptions import TokenError
from ninja_jwt.tokens import RefreshToken

from .models import Profile, User  # 追加
```

✅ 検証済み: ruff の import 順チェックも通過

ファイルの最後（refresh の下）に追加

```python
class RegisterIn(Schema):
    username: str = Field(min_length=1, max_length=150)
    password: str = Field(min_length=8)  # 短すぎるパスワードは 422


class UserOut(Schema):
    id: int
    username: str  # password は返さない（書かない項目は応答に出ない）


class ProfileOut(Schema):
    user_id: int
    bio: str


class ProfileIn(Schema):
    bio: str


@router.post("/register", response={201: UserOut, 409: ErrorOut})
def register(request: HttpRequest, payload: RegisterIn):
    if User.objects.filter(username=payload.username).exists():
        return Status(409, {"detail": "そのユーザー名は使われています"})
    # create_user: パスワードをハッシュにしてから保存する
    user = User.objects.create_user(username=payload.username, password=payload.password)
    Profile.objects.create(user=user)  # 空のプロフィールを一緒に作る
    return Status(201, user)


@router.get("/me", response=ProfileOut, auth=JWTAuth())
def get_my_profile(request: HttpRequest):
    # user_id は一意なので、見つかるのは0件か1件
    return get_object_or_404(Profile, user_id=request.user.id)


@router.patch("/me", response=ProfileOut, auth=JWTAuth())
def update_my_profile(request: HttpRequest, payload: ProfileIn):
    profile = get_object_or_404(Profile, user_id=request.user.id)
    profile.bio = payload.bio
    profile.save()
    return profile
```

✅ 検証済み: django-ninja 1.7.1 / django-ninja-jwt 5.4.5（ruff・mypy も通過）

**③ 叩いてみる**

```bash
# 登録 → 201。もう一度同じ名前で → 409
curl -s -X POST http://127.0.0.1:8000/api/auth/register -H "Content-Type: application/json" \
  -d '{"username": "carol", "password": "pass1234"}'
# carol でログインして、身分証を ACCESS に入れる（2-6 ④と同じ形）
ACCESS=$(curl -s -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "carol", "password": "pass1234"}' \
  | uv run python -c "import json, sys; print(json.load(sys.stdin)['access'])")
# 自分のプロフィールを書き換える
curl -s -X PATCH http://127.0.0.1:8000/api/auth/me -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" -d '{"bio": "よろしく"}'
```

```text
{"id": 3, "username": "carol"}
{"detail": "そのユーザー名は使われています"}
{"user_id": 3, "bio": "よろしく"}
```

✅ 検証済み: 201 / 409 / 200。短いパスワードは 422、身分証なしの `/me` は 401（日本語は `\u…` を直して表示。`id` は環境で変わる）

```bash
# ②より前からいるユーザーには Profile が無く、/me が 404 になる。作っておく（1人1回。名前は自分のものに）
uv run python manage.py shell -c "from accounts.models import Profile, User; print(Profile.objects.create(user=User.objects.get(username='alice')))"
```

✅ 検証済み: `1 のプロフィール` のように表示される。2回目は `IntegrityError (1062, "Duplicate entry ...")`

**④ テスト**（`tests/test_register.py` 新規・全文。`# TODO` の下は先に自分で書く）

```python
import pytest
from ninja.testing import TestClient

from accounts.models import Profile, User
from config.api import api

client = TestClient(api)


@pytest.mark.django_db
def test_register_creates_user_and_profile() -> None:
    res = client.post("/auth/register", json={"username": "carol", "password": "pass1234"})
    # TODO: 201 で、応答に password が無く、carol の Profile が1つできていること
    assert res.status_code == 201
    assert "password" not in res.json()
    assert Profile.objects.filter(user_id=res.json()["id"]).count() == 1


@pytest.mark.django_db
def test_registered_user_can_login() -> None:
    client.post("/auth/register", json={"username": "carol", "password": "pass1234"})
    res = client.post("/auth/login", json={"username": "carol", "password": "pass1234"})
    # TODO: 登録したパスワードでログインできること（200）
    assert res.status_code == 200


def test_duplicate_username_is_409(user: User) -> None:
    res = client.post("/auth/register", json={"username": user.username, "password": "pass1234"})
    # TODO: 409 で、ユーザーが増えていないこと
    assert res.status_code == 409
    assert User.objects.count() == 1


def test_update_my_profile(user: User, auth_headers: dict[str, str]) -> None:
    Profile.objects.create(user=user)
    res = client.patch("/auth/me", json={"bio": "よろしく"}, headers=auth_headers)
    # TODO: 200 で、DB の bio が書き換わっていること
    assert res.status_code == 200
    assert Profile.objects.get(user=user).bio == "よろしく"
```

✅ 検証済み: pytest-django 4.14.0（`21 passed`。ruff・mypy も通過）

### 8-2. 🔬 仕組み解剖

| | `create_user()` | `OneToOneField` |
| --- | --- | --- |
| 正式名称 | `UserManager.create_user()` | `django.db.models.OneToOneField` |
| いつ・誰が | 呼んだとき。Django がパスワードを**ハッシュ**にしてから保存する | マイグレーション時に `UNIQUE` 付きの列になる。`user.profile` で逆向きにも引ける |
| 発行される SQL | `INSERT INTO accounts_user (password, ...) VALUES ('pbkdf2_sha256$1000000$...', ...)` | `user.profile` を読むと `SELECT ... FROM accounts_profile WHERE user_id = 1 LIMIT 21` |
| TS での対応物 | 対応物なし。Node では bcrypt でハッシュを自分で作る | 対応物なし（ORM の機能） |
| なぜこの設計 | 平文で保存する事故を防ぐ | 「1人に1つ」を DB が守る |
| 失敗すると | 同じ名前は `IntegrityError` で 500。だから②は先に `exists()` で 409 を返す | 2つ目は `IntegrityError (1062)`。無いものを `user.profile` で読むと `RelatedObjectDoesNotExist` |

✅ 検証済み: Django 5.2.17（SQL は `CaptureQueriesContext` で確認。登録1回で SELECT 1本 + INSERT 2本）

> 🧒 **かみくだくと**: **ハッシュ**は、パスワードを決まった手順で崩した文字列。元には戻せない。
> ログインでは、入力を同じ手順で崩して比べる。

```text
accounts_user                accounts_profile
+----+----------+            +----+-------------+------------------+
| id | username |            | id | bio         | user_id (UNIQUE) |
+----+----------+            +----+-------------+------------------+
|  1 | alice    | <--------- |  1 | ""          |                1 |
|  3 | carol    | <--------- |  2 | "yoroshiku" |                3 |
+----+----------+            +----+-------------+------------------+
```

✅ 検証済み: 上の SQL どおりの形（`user_id` に同じ値は2回入らない）

見てほしいのは、矢印の根元の **`UNIQUE`** です。外せば 2-2 と同じ多対一になります。

### 8-3. 🐍 Python注

このステップに新しい Python の文法はありません。

### 8-4. 解説 — なぜこう設計するか

自己紹介はログインに使いません。だから User に足さず、別の台帳に分けます。

🧠 Django の考え方: 認証に使う情報は User に、それ以外は一対一の別モデルに。

> ⏭️ **後で回収**: ②は User と Profile を別々に INSERT する。2本目が失敗すると、Profile の無い User が残る。
> 「全部か、何もしないか」にする方法（トランザクション）は第3部-3で扱う。

### 8-5. 🏢 実務メモ ／ 🔓 教材用の簡略化

> 🏢 **実務メモ**: 認証に関係ない情報は、一対一の別モデルに置く。公式ドキュメントもこの形を案内している。
> 根拠: https://docs.djangoproject.com/en/5.2/topics/auth/customizing/#extending-the-existing-user-model

> 🔓 **教材用の簡略化**: パスワードの条件は「8文字以上」だけ。
> **本番では**: `validate_password()` で、よくあるパスワードも弾く。
> 根拠: https://docs.djangoproject.com/en/5.2/topics/auth/passwords/#module-django.contrib.auth.password_validation

### 8-6. 🔮 予測 → 動作確認

1. ②の `create_user` を `User.objects.create` に変えて登録すると、ログインできる？
2. 登録 API を1回呼ぶと、SQL は何本？
3. 同じユーザーに Profile を2つ作ろうとすると？

<details><summary>答え</summary>

1. できない（401）。`pass1234` が平文のまま入り、照合が合わない（検証済み）
2. 3本。名前の確認（`SELECT 1 ... LIMIT 1`）、User の INSERT、Profile の INSERT
3. `IntegrityError (1062, "Duplicate entry '1' for key 'accounts_profile.user_id'")`。DB の `UNIQUE` が止める

</details>

### 8-7. ✅ 想起チェック

1. `OneToOneField` と `ForeignKey` は、テーブルの上で何が違う？
2. `create_user()` が `objects.create()` と違うところは？

<details><summary>答え</summary>

1. つなぐ列に `UNIQUE` が付くかどうか
2. パスワードをハッシュにしてから保存する

</details>

### 8-8. 📇 まとめカード

この回で覚えることは1つだけ: **ユーザーは `create_user()` で作り、User に足したい情報は `OneToOneField` の別モデルに置く。**

📒 用語集に追記: 一対一 / ハッシュ / `create_user()`

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第2部 ステップ9` — コメントと返信（自己参照）

---

## 第2部-9: コメントと返信（自己参照）

**❓ この回の問い**: 2-8 で、User と Profile を一対一でつないだ。では、同じ台帳の行どうしをつなぐには？

**作るもの**: 記事へのコメントと、コメントへの返信（`/api/posts/{post_id}/comments`）
**重要度**: 🟡 読めればよい — 自分で書く頻度は低いが、コメント・カテゴリの階層・組織図などで出会う
**前ステップとの接続**: 2-2 の `ForeignKey` の行き先を、自分自身の台帳にする

### 9-0. このステップの初出

**Django / Ninja**: `ForeignKey("self")`, `related_name` / **Python**: `assert`

> 🧒 **かみくだくと**: **自己参照**は、台帳の行が、同じ台帳の別の行を指すこと。
> 返信は「どのコメントへの返信か」を、同じコメント台帳の `id` で覚える。

### 9-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

**① Comment を作る**（`blog/models.py` のファイルの最後に追加。既存のモデルは消さない）

```python
class Comment(models.Model):
    # related_name: 記事の側から post.comments で引けるようにする
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # 自己参照: 返信なら返信先のコメント。最初のコメントなら空
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,  # 親コメントを消すと、返信も消える
        null=True,
        blank=True,
        related_name="replies",  # 親コメントから comment.replies で返信を引く
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.body[:20]
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17（ruff・mypy も通過）

`blog/admin.py`（全文。データを見るための窓に Comment も足す）

```python
from django.contrib import admin

from .models import Category, Comment, Post, Tag

# Post を管理画面に出す（見た目の調整はしない）
admin.site.register(Post)
admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(Comment)
```

✅ 検証済み: 管理画面に Comments が出る

```bash
uv run python manage.py makemigrations blog
SQL_LOG=0 uv run python manage.py sqlmigrate blog 0005
uv run python manage.py migrate
```

```sql
CREATE TABLE `blog_comment` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `body` longtext NOT NULL, `created_at` datetime(6) NOT NULL, `author_id` bigint NOT NULL, `parent_id` bigint NULL, `post_id` bigint NOT NULL);
ALTER TABLE `blog_comment` ADD CONSTRAINT `blog_comment_parent_id_f2a027bb_fk_blog_comment_id` FOREIGN KEY (`parent_id`) REFERENCES `blog_comment` (`id`);
-- （author_id と post_id の外部キー2本は省略）
```

✅ 検証済み: MySQL 8.4.11（制約名の末尾は環境で変わる）

見てほしいのは `REFERENCES blog_comment` です。外部キーの行き先が、**自分と同じ台帳**になっています。

**② コメントの API**（`blog/api.py`。import の1行を置き換え、ファイルの最後に追加）

import の1行（この形に置き換える）

```python
from .models import Category, Comment, Post, Tag
```

✅ 検証済み: ruff の import 順チェックも通過

ファイルの最後（delete_post の下）に追加

```python
class CommentIn(Schema):
    body: str = Field(min_length=1)
    parent_id: int | None = None  # 返信なら返信先のコメントの id


class ReplyOut(Schema):
    id: int
    author_id: int
    body: str
    created_at: datetime


class CommentOut(ReplyOut):
    replies: list[ReplyOut]  # 入れ子: このコメントへの返信


@router.post("/{post_id}/comments", response={201: CommentOut}, auth=JWTAuth())
def create_comment(request: HttpRequest, post_id: int, payload: CommentIn):
    post = get_object_or_404(Post, id=post_id)
    parent = None
    if payload.parent_id is not None:
        # 返信先は、同じ記事のコメントに限る（違う記事なら 404）
        parent = get_object_or_404(Comment, id=payload.parent_id, post=post)
        if parent.parent_id is not None:
            raise HttpError(400, "返信には返信できません")
    # JWTAuth を通ったので必ずログイン済み。mypy に「User だ」と伝える
    assert request.user.is_authenticated
    comment = Comment.objects.create(
        post=post, author=request.user, parent=parent, body=payload.body
    )
    return Status(201, comment)


@router.get("/{post_id}/comments", response=list[CommentOut])
def list_comments(request: HttpRequest, post_id: int):
    post = get_object_or_404(Post, id=post_id)
    # post.comments: related_name で付けた、記事からコメントへの入口
    return post.comments.filter(parent=None).prefetch_related("replies")
```

✅ 検証済み: django-ninja 1.7.1（ruff・mypy も通過）

**③ 叩いてみる**（`ACCESS` は 2-6 ④の方法で入れておく。記事の id は自分の環境のもの）

```bash
curl -s -X POST http://127.0.0.1:8000/api/posts/1/comments -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" -d '{"body": "最初のコメント"}'
# 返信: parent_id に、上で返ってきた id を入れる
curl -s -X POST http://127.0.0.1:8000/api/posts/1/comments -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" -d '{"body": "返信です", "parent_id": 1}'
curl -s http://127.0.0.1:8000/api/posts/1/comments
```

```text
{"id": 1, "author_id": 1, "body": "最初のコメント", "created_at": "...", "replies": []}
{"id": 2, "author_id": 1, "body": "返信です", "created_at": "...", "replies": []}
[{"id": 1, ..., "replies": [{"id": 2, "author_id": 1, "body": "返信です", "created_at": "..."}]}]
```

✅ 検証済み: 201 / 201 / 200。返信の返信は 400、身分証なしは 401、無い記事は 404（日本語は `\u…` を直して表示）

**④ テスト**（`tests/test_comments.py` 新規）

フィクスチャは3回目なので、要件だけ書きます。先に自分で書いてから、解答例と比べてください。

1. 最初のコメントと返信を作ると、一覧の一番上には最初のコメントだけが出て、返信は `replies` の中に入る
2. 別の記事のコメントに返信しようとすると 404 で、コメントは増えない
3. 返信に返信しようとすると 400
4. 親コメントを消すと、返信も消える

<details><summary>解答例</summary>

```python
from ninja.testing import TestClient

from accounts.models import User
from blog.models import Comment, Post
from config.api import api

client = TestClient(api)


def test_reply_is_nested(user: User, auth_headers: dict[str, str]) -> None:
    post = Post.objects.create(title="t", body="b", author=user)
    url = f"/posts/{post.id}/comments"
    first = client.post(url, json={"body": "最初"}, headers=auth_headers).json()
    client.post(url, json={"body": "返信", "parent_id": first["id"]}, headers=auth_headers)

    res = client.get(url)
    assert res.status_code == 200
    assert len(res.json()) == 1  # 一覧の一番上には、最初のコメントだけ
    assert res.json()[0]["replies"][0]["body"] == "返信"


def test_reply_to_other_posts_comment_is_404(user: User, auth_headers: dict[str, str]) -> None:
    post_a = Post.objects.create(title="a", body="b", author=user)
    post_b = Post.objects.create(title="b", body="b", author=user)
    other = Comment.objects.create(post=post_b, author=user, body="b の記事のコメント")

    res = client.post(
        f"/posts/{post_a.id}/comments",
        json={"body": "x", "parent_id": other.id},
        headers=auth_headers,
    )
    assert res.status_code == 404
    assert Comment.objects.count() == 1


def test_reply_to_reply_is_400(user: User, auth_headers: dict[str, str]) -> None:
    post = Post.objects.create(title="t", body="b", author=user)
    first = Comment.objects.create(post=post, author=user, body="最初")
    reply = Comment.objects.create(post=post, author=user, parent=first, body="返信")

    res = client.post(
        f"/posts/{post.id}/comments",
        json={"body": "返信の返信", "parent_id": reply.id},
        headers=auth_headers,
    )
    assert res.status_code == 400


def test_deleting_parent_deletes_replies(user: User) -> None:
    post = Post.objects.create(title="t", body="b", author=user)
    first = Comment.objects.create(post=post, author=user, body="最初")
    Comment.objects.create(post=post, author=user, parent=first, body="返信")

    first.delete()
    assert Comment.objects.count() == 0
```

</details>

✅ 検証済み: pytest-django 4.14.0（`25 passed`。ruff・mypy も通過）

> 💡補足: `@pytest.mark.django_db` が無くても DB を使えるのは、どのテストも `user` を受け取るから。conftest の `def user(db)` の `db` は pytest-django のフィクスチャで、マークと同じく DB を使えるようにする。`user` を受け取らないテストには、今までどおりマークが要る。

### 9-2. 🔬 仕組み解剖

| | `ForeignKey("self")` | `related_name` |
| --- | --- | --- |
| 正式名称 | 再帰的な関係（recursive relationship） | `ForeignKey(related_name=...)` |
| いつ・誰が | マイグレーション時に、自分の台帳を指す外部キーになる | 起動時に、相手のモデルへ逆向きの入口（`post.comments`）を付け足す |
| 発行される SQL | 親を消すと、返信を探して返信ごと DELETE する（下の図） | `post.comments.filter(parent=None)` → `WHERE post_id = 1 AND parent_id IS NULL` |
| TS での対応物 | 対応物なし（ORM の機能） | 対応物なし（ORM の機能） |
| なぜこの設計 | 返信の台帳を別に作らず、深さが変わっても同じ形で持てる | 既定の名前（`comment_set`）より読みやすい。逆向きの名前がぶつかるときにも使う |
| 失敗すると | `"self"` を `Comment` と書くと、クラスがまだできていないので `NameError` | 同じ名前がぶつかると、起動時のチェックでエラー（`fields.E304`） |

✅ 検証済み: Django 5.2.17（SQL は `CaptureQueriesContext` で確認）

```text
blog_comment
+----+---------+-----------+----------+
| id | post_id | parent_id | body     |
+----+---------+-----------+----------+
|  1 |       1 |      NULL | first    | <--+
|  2 |       1 |         1 | reply    | ---+
|  3 |       1 |      NULL | second   |
+----+---------+-----------+----------+
```

✅ 検証済み: ③の2件に、最初のコメントをもう1件足したときの台帳（body は英語に置き換えた）

見てほしいのは、矢印が**同じ台帳の中で**折り返している点です。`parent_id` が NULL の行が、最初のコメントです。

一覧の GET は SQL 3本です。記事を1本、最初のコメントを1本、`prefetch_related("replies")` で全部の返信を `WHERE parent_id IN (1, 3)` の1本で取ります（2-4 と同じ）。

### 9-3. 🐍 Python注

> 🐍 **Python注**: `assert 条件` は「ここでは必ず条件が真」という宣言。偽なら `AssertionError` で止まる。
> mypy は、この宣言のあとの `request.user` を `User` として扱う。
> `self.body[:20]` は、先頭の20文字を取り出す（TS の `body.slice(0, 20)`）。

### 9-4. 解説 — なぜこう設計するか

返信の深さを1段に絞ったのは、一覧の SQL を3本で止めるためです。深さに上限が無いと、段の数だけ SQL が増えます。

🧠 Django の考え方: 関係の形はモデルで自由に持てる。どこまで許すかは API で決める。

### 9-5. 🏢 実務メモ

> 🏢 **実務メモ**: 逆向きの入口には `related_name` で名前を付けておくと、`post.comments` のように読める。
> 根拠: https://docs.djangoproject.com/en/5.2/ref/models/fields/#django.db.models.ForeignKey.related_name

### 9-6. 🔮 予測 → 動作確認

1. 返信が3件ある親コメントを消すと、何件消える？
2. ②の `prefetch_related("replies")` を外すと、最初のコメントが10件のとき SQL は何本？

<details><summary>答え</summary>

1. 4件。返信も CASCADE で消える。Django は先に返信を探してから、まとめて DELETE する（検証済み）
2. 12本。記事1本 + 最初のコメント1本 + 返信を10回（2-4 の N+1）

</details>

### 9-7. ✅ 想起チェック

1. `ForeignKey("self")` の `"self"` は、何を指す？
2. `related_name="replies"` を付けると、何ができるようになる？

<details><summary>答え</summary>

1. 定義しているモデル自身（ここでは Comment）
2. 親コメントから `comment.replies.all()` で返信を引ける

</details>

### 9-8. 📇 まとめカード

この回で覚えることは1つだけ: **`ForeignKey("self")` で同じ台帳の行どうしをつなぎ、逆向きの名前は `related_name` で付ける。**

📒 用語集に追記: 自己参照 / `related_name` / `assert`

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第2部 ステップ10` — 画像アップロード

---

## 第2部-10: 画像アップロード

**❓ この回の問い**: 2-9 までで、記事にいろいろな「文字」をぶら下げた。では、画像のような「ファイル」はどこに、どう置く？

**作るもの**: 記事に画像を付ける `POST /api/posts/{post_id}/images`（1記事に何枚でも）
**重要度**: 🔴 毎日使う — 画像・添付ファイルは、ほとんどの Web サービスにある
**前ステップとの接続**: 2-9 の「記事にぶら下がる台帳」を、画像のために1つ足す

### 10-0. このステップの初出

**Django / Ninja**: `ImageField` と `MEDIA_ROOT`, `UploadedFile` / **Python**: `a, b = ...`（分割代入）

> 🧒 **かみくだくと**: **メディアファイル**は、利用者が送ってきたファイル（画像など）のこと。
> Django は、ファイルの中身を**ディスク**に置き、台帳には**置き場所の文字列だけ**を書く。

### 10-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

**① Pillow を入れる**

`ImageField` が画像を読むのに使う、Python の画像ライブラリです。

```bash
uv add pillow
```

✅ 検証済み: Pillow 13.0.0 が入る

**② ファイルの置き場所を決める**

`config/settings.py`（`STATIC_URL = "static/"` の下に追加）

```python
# アップロードされたファイルの置き場所と、それを配る URL の頭
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "media/"
```

✅ 検証済み: Django 5.2.17

`config/urls.py`（全文）

```python
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from blog import views
from config.api import api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("manual/posts/", views.post_list),  # 1-5・1-6 の手書き版（比較用に残す）
    path("api/", api.urls),  # Ninja の API 一式
]

# 開発中だけ、/media/ の URL でアップロードされたファイルを配る（DEBUG=False では何もしない）
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

✅ 検証済み: `/media/posts/red.png` が `200 image/png` で返る

`media/` は `.gitignore` 済みなので、画像は git に入りません。

**③ PostImage を作る**（`blog/models.py` のファイルの最後に追加。既存のモデルは消さない）

```python
class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="images")
    # ファイルは MEDIA_ROOT/posts/ に置き、台帳にはパスの文字列だけを入れる
    image = models.ImageField(upload_to="posts/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.image.name
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17（ruff・mypy も通過）

`blog/admin.py`（全文。データを見るための窓に PostImage も足す）

```python
from django.contrib import admin

from .models import Category, Comment, Post, PostImage, Tag

# Post を管理画面に出す（見た目の調整はしない）
admin.site.register(Post)
admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(Comment)
admin.site.register(PostImage)
```

✅ 検証済み: 管理画面に Post images が出る

```bash
uv run python manage.py makemigrations blog
SQL_LOG=0 uv run python manage.py sqlmigrate blog 0006
uv run python manage.py migrate
```

```sql
CREATE TABLE `blog_postimage` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `image` varchar(100) NOT NULL, `created_at` datetime(6) NOT NULL, `post_id` bigint NOT NULL);
ALTER TABLE `blog_postimage` ADD CONSTRAINT `blog_postimage_post_id_09cc1915_fk_blog_post_id` FOREIGN KEY (`post_id`) REFERENCES `blog_post` (`id`);
```

✅ 検証済み: MySQL 8.4.11（制約名の末尾は環境で変わる）

見てほしいのは `image varchar(100)` です。画像の列なのに、ただの**文字列**の列です。

**④ 画像を受け取る API**（`blog/api.py`。import を3行置き換え、ファイルの最後に追加）

import の3行（それぞれ、この形に置き換える。1行目は新しく足す）

```python
from django.core.files.images import get_image_dimensions
```

```python
from ninja import Field, Router, Schema, Status, UploadedFile
```

```python
from .models import Category, Comment, Post, PostImage, Tag
```

✅ 検証済み: ruff の import 順チェックも通過（1行目は `from django.http import HttpRequest` の上に置く）

ファイルの最後（list_comments の下）に追加

```python
class PostImageOut(Schema):
    id: int
    url: str = Field(alias="image.url")  # 保存したファイルを見に行く URL


@router.post("/{post_id}/images", response={201: PostImageOut}, auth=JWTAuth())
def upload_image(request: HttpRequest, post_id: int, file: UploadedFile):
    post = get_object_or_404(Post, id=post_id)
    if post.author_id != request.user.id:
        raise HttpError(403, "自分の記事にしか画像を付けられません")
    # 大きすぎるファイルは断る（size は不明のとき None になりうる）
    if file.size is None or file.size > 2 * 1024 * 1024:
        raise HttpError(400, "画像は 2MB までです")
    # Pillow で中身を読んで、本当に画像か確かめる（画像でなければ幅と高さが None）
    width, _ = get_image_dimensions(file)
    if width is None:
        raise HttpError(400, "画像ファイルを送ってください")
    post_image = PostImage.objects.create(post=post, image=file)
    return Status(201, post_image)
```

✅ 検証済み: django-ninja 1.7.1（ruff・mypy も通過）

**⑤ 叩いてみる**（`ACCESS` は 2-6 ④の方法で、直前に入れ直す。記事の id は自分の記事のもの）

```bash
# 試し用の赤い四角の画像を作る（64x64 の PNG）
uv run python -c "from PIL import Image; Image.new('RGB', (64, 64), 'red').save('red.png')"
# -F は「ファイルを添えて送る」。file= は upload_image の引数の名前と揃える
curl -s -X POST http://127.0.0.1:8000/api/posts/1/images \
  -H "Authorization: Bearer $ACCESS" -F "file=@red.png"
```

```text
{"id": 1, "url": "/media/posts/red.png"}
```

✅ 検証済み: 201。画像でないファイルは 400、他人の記事は 403、身分証なしは 401、2MB 超は 400

`http://127.0.0.1:8000/media/posts/red.png` をブラウザで開くと、赤い四角が見えます。

**⑥ テスト**（`tests/test_images.py` 新規）

要件だけ書きます。使う道具: `SimpleUploadedFile(名前, バイト列)`（テスト用のファイル）、`client.post(url, FILES={"file": ...})`、`settings` フィクスチャ（そのテストの間だけ設定を変える）、`tmp_path`（使い捨てのフォルダ）。

1. PNG を送ると 201 で、`url` が `/media/posts/red.png`。ファイルもできている
2. 画像でないファイルは 400 で、PostImage は増えない
3. 他人の記事に送ると 403
4. ファイルは本物の `media/` ではなく `tmp_path` に置く

<details><summary>解答例</summary>

```python
import io
from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from ninja.testing import TestClient
from PIL import Image

from accounts.models import User
from blog.models import Post, PostImage
from config.api import api

client = TestClient(api)


@pytest.fixture(autouse=True)
def media_in_tmp(settings, tmp_path: Path) -> None:
    # テストで保存するファイルは、使い捨てのフォルダに置く（本物の media/ を汚さない）
    settings.MEDIA_ROOT = tmp_path


def png_file(name: str = "red.png") -> SimpleUploadedFile:
    # Pillow で 1x1 の PNG を作り、アップロードされたファイルの形にする
    buf = io.BytesIO()
    Image.new("RGB", (1, 1), "red").save(buf, "PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


def test_upload_saves_file(user: User, auth_headers: dict[str, str], tmp_path: Path) -> None:
    post = Post.objects.create(title="t", body="b", author=user)
    res = client.post(f"/posts/{post.id}/images", FILES={"file": png_file()}, headers=auth_headers)
    assert res.status_code == 201
    assert res.json()["url"] == "/media/posts/red.png"
    assert (tmp_path / "posts" / "red.png").exists()  # ファイルが MEDIA_ROOT に置かれた


def test_not_image_is_400(user: User, auth_headers: dict[str, str]) -> None:
    post = Post.objects.create(title="t", body="b", author=user)
    fake = SimpleUploadedFile("fake.png", b"hello", content_type="image/png")
    res = client.post(f"/posts/{post.id}/images", FILES={"file": fake}, headers=auth_headers)
    assert res.status_code == 400
    assert PostImage.objects.count() == 0


def test_other_users_post_is_403(auth_headers: dict[str, str]) -> None:
    bob = User.objects.create_user(username="bob", password="pass1234")
    post = Post.objects.create(title="t", body="b", author=bob)
    res = client.post(f"/posts/{post.id}/images", FILES={"file": png_file()}, headers=auth_headers)
    assert res.status_code == 403
```

</details>

✅ 検証済み: pytest-django 4.14.0（`28 passed`。ruff・mypy も通過）

> 💡補足: `autouse=True` のフィクスチャは、引数に書かなくても、このファイルの全テストで使われる。

### 10-2. 🔬 仕組み解剖

| | `ImageField` と `MEDIA_ROOT` | `UploadedFile` |
| --- | --- | --- |
| 正式名称 | `models.ImageField` / `settings.MEDIA_ROOT`・`MEDIA_URL` | `ninja.UploadedFile`（中身は Django の `UploadedFile`） |
| いつ・誰が | 保存のときに Django が、ファイルを `MEDIA_ROOT/posts/` に書き、台帳にパスを INSERT する | リクエストごとに Django が、ファイル付きの送信を読み取る。Ninja は引数の名前（`file`）で取り出して渡す |
| 発行される SQL | `INSERT INTO blog_postimage (post_id, image, created_at) VALUES (1, 'posts/red.png', ...)` | なし（ファイルはまだメモリか一時ファイルの中） |
| TS での対応物 | 対応物なし（ファイルの置き場所まで面倒を見る ORM の機能） | ブラウザの `File`（`FormData` に入れて送るもの）を、受け取る側から見たもの |
| なぜこの設計 | DB は大きなバイト列が苦手。中身はディスク、台帳は場所だけにすると、置き場所を後で入れ替えられる | ファイルを JSON の中に入れると大きく膨らむ。ファイルは別の送り方（下の 🧒）で受け取る |
| 失敗すると | Pillow が無いと、起動時のチェックでエラー（`fields.E210`） | `file` を送らないと 422（`"msg": "Field required"`） |

✅ 検証済み: Django 5.2.17（SQL は `CaptureQueriesContext` で確認。ほかに身分証の User と記事の SELECT が1本ずつ）

> 🧒 **かみくだくと**: **multipart/form-data** は、文字とファイルを「区切り線」で仕切って、1回で送る形式。`curl -F` やブラウザの `FormData` がこの形で送る。

```text
curl -F "file=@red.png"
        |
        v
  upload_image() --- writes the file --> media/posts/red.png      (disk)
        |
        +--- INSERT --> blog_postimage.image = 'posts/red.png'     (DB)

browser: GET /media/posts/red.png --> static() reads the file on disk
```

✅ 検証済み: ⑤のあと `media/posts/red.png` ができ、台帳の `image` 列は `posts/red.png`

見てほしいのは、行き先が**2つ**に分かれる点です。

### 10-3. 🐍 Python注

> 🐍 **Python注**: `width, _ = get_image_dimensions(file)` は分割代入。2つの値を順に受け取る（TS の `const [width, _] = ...`）。
> `_` は「使わない値」の置き場という慣習。

### 10-4. 解説 — なぜこう設計するか

`ImageField` は、モデルで保存するときには中身を確かめません。画像の検査はフォーム（SSR の部品）の側にあるからです。そこで④では `get_image_dimensions` で自分で確かめています。外すと、文字だけのファイルも 201 で保存されます（検証済み）。

🧠 Django の考え方: 中身はストレージ（ファイルの置き場所）、台帳には場所だけ。置き場所は設定で差し替える。

### 10-5. ⚠️ アンチパターン ／ 🔓 教材用の簡略化

> ⚠️ **アンチパターン**: 拡張子や `Content-Type` だけで「画像だ」と信じる。どちらも送る側が自由に書ける。中身を読み、大きさにも上限を付ける。
> 根拠: https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html#content-type-validation

> 🔓 **教材用の簡略化**: 画像を、アプリと同じマシンの `media/` に置き、Django 自身が配っている。
> **本番では**: ストレージを S3 などに差し替え、配るのは Web サーバや CDN に任せる。`static()` は `DEBUG=False` では何もしない。
> 根拠: https://docs.djangoproject.com/en/5.2/howto/static-files/#serving-files-uploaded-by-a-user-during-development

### 10-6. 🔮 予測 → 動作確認

1. 同じ `red.png` をもう1回送ると、返ってくる `url` は？
2. 画像を付けた記事を消すと、PostImage の行と、`media/` のファイルはどうなる？
3. 画像を1枚送ると、SQL は何本？

<details><summary>答え</summary>

1. `/media/posts/red_n7ZMuoN.png` のように、`_` とランダムな7文字が付く。上書きを避けるため（検証済み）
2. 行は CASCADE で消えるが、**ファイルは残る**（検証済み。根拠: https://docs.djangoproject.com/en/5.2/ref/models/fields/#django.db.models.fields.files.FieldFile.delete）
3. 3本。身分証の User、記事、INSERT（検証済み）

</details>

### 10-7. ✅ 想起チェック

1. `blog_postimage` の `image` 列には、何が入っている？
2. `upload_to="posts/"` は、何を決めている？

<details><summary>答え</summary>

1. ファイルの置き場所を表す文字列（`posts/red.png`）。画像の中身は入っていない
2. `MEDIA_ROOT` の中の、どのフォルダに置くか

</details>

### 10-8. 📇 まとめカード

この回で覚えることは1つだけ: **ファイルの中身は `MEDIA_ROOT` の下に、台帳には場所の文字列だけ。画像かどうかは自分で確かめる。**

📒 用語集に追記: メディアファイル / `MEDIA_ROOT`・`MEDIA_URL` / `ImageField` / `UploadedFile` / multipart/form-data

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第2部 ステップ11` — 検索と絞り込み

---

## 第2部-11: 検索と絞り込み

**❓ この回の問い**: 2-10 までで、記事にカテゴリ・タグ・コメント・画像が付いた。記事が増えたら、欲しい記事だけをどう取り出す？

**作るもの**: `GET /api/posts?q=ninja&category_id=2` で、検索とカテゴリの絞り込みができる一覧
**重要度**: 🔴 毎日使う — 一覧 API には、ほぼ必ず検索や絞り込みが付く
**前ステップとの接続**: 2-4 の `list_posts` に、`filter()` を重ねる

### 11-0. このステップの初出

**Django / Ninja**: フィールドルックアップ（`__icontains`）, `Q` / **Python**: `if q:`（空の文字列は偽）

> 🧒 **かみくだくと**: **フィールドルックアップ**は、`項目名__比べ方` の形で「どう比べるか」を書く方法。
> `title__icontains="ninja"` は「title に ninja を含む（大文字・小文字は区別しない）」。

> 🧒 **かみくだくと**: **クエリパラメータ**は、URL の `?` の後ろ（`?q=ninja&category_id=2`）の部分。
> Ninja では、関数の引数のうち、パス（`{post_id}`）に無いものがクエリパラメータになる。

### 11-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

**① 一覧に検索を足す**（`blog/api.py`。import を1行足し、`list_posts` を丸ごと置き換える）

import の1行（`from django.http import HttpRequest` の上に足す）

```python
from django.db.models import Q
```

✅ 検証済み: ruff の import 順チェックも通過

`list_posts`（デコレータの行から `return` までを、この形に置き換える）

```python
@router.get("", response=list[PostOut])
def list_posts(request: HttpRequest, q: str | None = None, category_id: int | None = None):
    posts = (
        Post.objects.select_related("category")  # カテゴリは JOIN で同じ SQL に入れる
        .prefetch_related("tags")  # タグは別の SQL 1本でまとめて取る
        .all()
    )
    if q:
        # タイトルか本文のどちらかに q を含む記事（大文字・小文字は区別しない）
        posts = posts.filter(Q(title__icontains=q) | Q(body__icontains=q))
    if category_id is not None:
        posts = posts.filter(category_id=category_id)
    return posts
```

✅ 検証済み: django-ninja 1.7.1（ruff・mypy も通過）

**② 叩いてみる**（`q` は、自分の記事のタイトルや本文にある言葉に変える）

```bash
curl -s "http://127.0.0.1:8000/api/posts?q=ninja"
curl -s "http://127.0.0.1:8000/api/posts?q=ninja&category_id=1"
# 日本語は --data-urlencode で送る（-G は「GET の ? の後ろに付ける」）
curl -s -G http://127.0.0.1:8000/api/posts --data-urlencode "q=日記"
```

✅ 検証済み: 記事「Ninja で作った」「今日の日記」「三つ目の投稿（本文に ninja）」で、1本目は1件目と3件目、3本目は「今日の日記」だけが返る。`?category_id=abc` は 422

URL は必ず `"` で囲みます。囲まないと、zsh が `?` をファイル名の記号と読んで `no matches found` になります。`&` も、囲まないと「後ろで実行」の記号になります。

1本目で実際に出る SQL（`WHERE` の部分）です。

```sql
WHERE (`blog_post`.`title` LIKE '%ninja%' OR `blog_post`.`body` LIKE '%ninja%')
```

✅ 検証済み: MySQL 8.4.11（`CaptureQueriesContext` で確認。SQL は 2-4 と同じ2本のまま）

**③ テスト**（`tests/test_search.py` 新規）

要件だけ書きます。記事を3件作るフィクスチャ（`posts`）を自分で作ってから、テストを書いてください。並び順はまだ決めていない（2-12 で扱う）ので、タイトルは集合（`{...}`）にして比べます。

1. `?q=NINJA` で、タイトルに Ninja を含む記事と、本文に ninja を含む記事の2件が当たる
2. `?q=`（空）だと、全部返る
3. `q` と `category_id` を両方付けると、両方に合う記事だけ

<details><summary>解答例</summary>

```python
import pytest
from ninja.testing import TestClient

from blog.models import Category, Post
from config.api import api

client = TestClient(api)


@pytest.fixture
def posts(db) -> None:
    # 検索の材料: 記事3件。カテゴリは「技術」1件と「日記」2件
    tech = Category.objects.create(name="技術")
    diary = Category.objects.create(name="日記")
    Post.objects.create(title="Ninja で作った", body="API を書いた", category=tech)
    Post.objects.create(title="今日の日記", body="django を少し触った", category=diary)
    Post.objects.create(title="三つ目の投稿", body="ninja の話はしない", category=diary)


def titles(url: str) -> set[str]:
    # 並び順はまだ決めていない（2-12 で扱う）ので、集合にして比べる
    return {p["title"] for p in client.get(url).json()}


def test_q_searches_title_and_body(posts: None) -> None:
    # 大文字・小文字は区別しない。タイトルと本文のどちらに含まれていても当たる
    assert titles("/posts?q=NINJA") == {"Ninja で作った", "三つ目の投稿"}


def test_empty_q_returns_all(posts: None) -> None:
    assert len(titles("/posts?q=")) == 3


def test_q_and_category_are_and(posts: None) -> None:
    diary = Category.objects.get(name="日記")
    assert titles(f"/posts?q=ninja&category_id={diary.id}") == {"三つ目の投稿"}
```

</details>

✅ 検証済み: pytest-django 4.14.0（`31 passed`。2-4 の SQL 本数のテストもそのまま通る。ruff・mypy も通過）

### 11-2. 🔬 仕組み解剖

| | フィールドルックアップ | `Q` |
| --- | --- | --- |
| 正式名称 | field lookups（`exact`・`icontains`・`gt` など） | `django.db.models.Q`（Q オブジェクト） |
| いつ・誰が | `filter()` のときに ORM が `WHERE` の部品にする。SQL が飛ぶのは、Ninja がレスポンスを作るとき（遅延評価） | `Q(...) \| Q(...)` で OR の部品を組み立てる。`filter()` を重ねた分は AND になる |
| 発行される SQL | MySQL では `icontains` も `LIKE '%ninja%'`。大文字・小文字を無視するのは MySQL の照合順序（下の 💡） | `(title LIKE ... OR body LIKE ...) AND category_id = 1` |
| TS での対応物 | 対応物なし（ORM の機能） | 対応物なし（ORM の機能） |
| なぜこの設計 | `__` で区切ると、比べ方もリレーション先（`category__name`）も同じ書き方で表せる | キーワード引数（`filter(a=1, b=2)`）は AND しか表せない。OR を表す部品が別に要る |
| 失敗すると | 綴りを間違えると `FieldError`（500）。`perhaps you meant icontains?` と候補が出る | `\|` を Python の `or` と書くと、エラーにならずに左の `Q` だけが効く（下の 🔮） |

✅ 検証済み: Django 5.2.17（FieldError と `or` の挙動はシェルで確認）

```text
posts = Post.objects.select_related(...)     SELECT ... FROM blog_post
  .filter(Q(title__icontains=q)              WHERE (title LIKE '%ninja%'
          | Q(body__icontains=q))                   OR body LIKE '%ninja%')
  .filter(category_id=category_id)             AND category_id = 1
```

✅ 検証済み: `?q=ninja&category_id=1` で出た SQL を短くしたもの

見てほしいのは、`filter()` を重ねるたびに `WHERE` に AND で足されていく点です。SQL はまだ飛んでいません。最後に1本になって飛びます。

> 💡補足: このリポジトリの MySQL の照合順序（文字の比べ方の決まり）は `utf8mb4_0900_ai_ci`。`ci` は大文字・小文字、`ai` はアクセントを区別しない。日本語では濁点も区別せず、`はは` と `パパ` が等しくなる（検証済み）。これは Django ではなく DB の設定（根拠: https://docs.djangoproject.com/en/5.2/ref/databases/#mysql-collation）。

### 11-3. 🐍 Python注

> 🐍 **Python注**: `if q:` は、`q` が `None` でも空の文字列 `""` でも偽になる（TS と同じ）。
> `{p["title"] for p in ...}` は集合を作る書き方。重複が消え、順番を持たない。

### 11-4. 解説 — なぜこう設計するか

`q` は `if q:`、`category_id` は `is not None` で分けています。`?q=` のような空の検索は「条件なし」として全部返すためです。一方、数値を `if category_id:` で見ると、`0` も偽になり「条件なし」と同じ扱いになります。数値は `None` かどうかだけを見ます。

🧠 Django の考え方: QuerySet は条件を積み重ねる設計図。条件を足しても、SQL は最後に1本だけ。

### 11-5. 🏢 実務メモ ／ ⚠️ アンチパターン

> 🏢 **実務メモ**: `LIKE '%ninja%'` は、前が `%` なので索引（目次）が使えず、全部の行を読む。記事が大量になったら全文検索や専用の検索エンジンに切り替える（拡張モジュール `search`）。
> 根拠: https://docs.djangoproject.com/en/5.2/topics/db/search/#standard-textual-queries

> ⚠️ **アンチパターン**: f 文字列で SQL を組み立てる（`f"... LIKE '%{q}%'"`）。`q` に `'` を混ぜられると、SQL を書き換えられる（SQL インジェクション）。ORM は値を SQL と別に渡すので安全。
> 根拠: https://docs.djangoproject.com/en/5.2/topics/security/#sql-injection-protection

### 11-6. 🔮 予測 → 動作確認

1. ①の `|` を `or` に変えて `?q=ninja` を叩くと、何件返る？（本文だけに ninja がある記事に注目）
2. `?q=日記` で、カテゴリ「日記」の記事は全部当たる？
3. `?category_id=abc` は、何番のステータスで返る？

<details><summary>答え</summary>

1. 本文だけに ninja がある記事が消える。`Q(...) or Q(...)` は、左の `Q` をそのまま返すだけだから。エラーにならないので気づきにくい（検証済み）
2. 当たらない。探しているのはタイトルと本文だけ。カテゴリ名でも探すなら `Q(category__name__icontains=q)` を足す
3. 422。Ninja が `int` に変換できず、`"loc": ["query", "category_id"]` を返す（検証済み）

</details>

### 11-7. ✅ 想起チェック

1. `title__icontains` の `__` の左と右は、それぞれ何？
2. `filter()` を2回重ねると、条件は AND と OR のどちらでつながる？

<details><summary>答え</summary>

1. 左が項目名（`title`）、右が比べ方（`icontains`）
2. AND。OR にしたいときは `Q(...) | Q(...)`

</details>

### 11-8. 📇 まとめカード

この回で覚えることは1つだけ: **`filter(項目名__比べ方=値)` で条件を書き、OR が要るときだけ `Q` を `|` でつなぐ。**

📒 用語集に追記: フィールドルックアップ / `Q` / クエリパラメータ / 照合順序

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第2部 ステップ12` — ページング
