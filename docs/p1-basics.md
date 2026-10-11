# 第1部 — Django の土台 → 手書き → Ninja → CRUD

> この教材は、1周目で全部分かるようには作られていません。
> あとから出てくるものが、前の意味を決めることが多いからです。
> 分からない箇所には `# TODO: わからん` とコメントを残して、先に進んでください。
> 1周したあと、その印だけを見返せば十分です。

---

## 第1部-1: プロジェクトを動かす

**❓ この回の問い**: 雛形はできた。Django は何を見て「どの DB・どの URL で」動くのか？

**作るもの**: MySQL につながった開発サーバが起動する
**重要度**: 🔴 毎日使う — 機能を足すたびに開く
**前ステップとの接続**: 環境準備（§2.4 まで）の雛形に、DB の接続先を足す

### 1-0. このステップの初出

**Django / Ninja**: `settings.py`, `urls.py` / **Python**: `os.environ`, `Path` の `/`

### 1-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

`config/settings.py`（差分。2か所を書き換える）

```python
# このサーバが受け付けるホスト名
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# （INSTALLED_APPS などはそのまま）

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",  # mysqlclient を使う
        "NAME": "blog",
        "USER": "django",
        "PASSWORD": "django",
        "HOST": "127.0.0.1",
        "PORT": "3307",  # compose.yaml で公開したポート
        "OPTIONS": {"charset": "utf8mb4"},  # 絵文字も保存できる文字コード
    }
}
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / MySQL 8.4.11（`uv run python manage.py check` → `System check identified no issues (0 silenced).`、ruff・mypy も通過）

```bash
docker compose up -d --wait
uv run python manage.py runserver
```

```text
System check identified no issues (0 silenced).
You have 18 unapplied migration(s). Your project may not work properly until you apply the migrations for app(s): admin, auth, contenttypes, sessions.
Run 'python manage.py migrate' to apply them.
Django version 5.2.17, using settings 'config.settings'
Starting development server at http://127.0.0.1:8000/
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / MySQL 8.4.11

> 🧒 **かみくだくと**: `runserver` は開発用の簡易サーバ。保存すると自動で再起動する。

> ⏭️ **後で回収**: この警告は「テーブルがまだ無い」の意味。1-3 で回収する。`migrate` はまだしない。

### 1-2. 🔬 仕組み解剖

| | `settings.py` | `urls.py` |
| --- | --- | --- |
| 正式名称 | 設定モジュール | URLconf（`ROOT_URLCONF` が指す） |
| いつ・誰が | Django 本体が**起動時に1回**読む | **リクエストごと**に `urlpatterns` を上から照合 |
| TS での対応物 | 対応物なし。Node には設定を1か所に集める標準が無い | React Router の経路の配列 |
| なぜこの設計 | Python なので環境変数の読み込みなどを書ける | URL の一覧が1か所に集まる |
| 失敗すると | DB 停止中は起動時に `OperationalError` | 一致なしは 404 |

```text
【起動時に1回】
  manage.py runserver
    └→ config/settings.py を読む（DB の場所・案内表の場所など）

【リクエストごと】
  GET /hello/（窓口に来た人）
    └→ config/urls.py の urlpatterns を上から照合（受付の案内表）
         ├─ "admin/" に一致     → 管理画面の処理へ（302）
         └─ どれにも一致しない  → 404
```

✅ 検証済み: 右側のステータスは 1-6 で実測した値

見てほしいのは、**読むタイミングが2種類ある**ことです。

> ⏭️ **後で回収**: `admin.site.urls`（管理画面の URL 一式）は 1-4 で扱う。

### 1-3. 🐍 Python注

> 🐍 `os.environ["X"]` は環境変数を辞書として引く。無いと `KeyError` で止まる。
> 🐍 `BASE_DIR / ".env"` の `/` はパスの連結。

### 1-4. 解説 — なぜこう設計するか

🧠 Django の考え方: 設定は `settings.py`、URL の入口は `urls.py` に集める。1か所を見れば分かる。

### 1-5. 🔓 教材用の簡略化

> 🔓 **教材用の簡略化**: `DEBUG = True`・`ALLOWED_HOSTS`・DB のパスワードを直接書いている。
> **本番では**: `DEBUG = False`（エラー画面に設定値が出る）。接続情報は環境変数へ（第2部-1）。
> 根拠: https://docs.djangoproject.com/en/5.2/ref/settings/#debug

### 1-6. 🔮 予測 → 動作確認

**予測してから**実行してください。

1. `/hello/` を開くと何が返る？（`urls.py` には `admin/` だけ）
2. MySQL を止めて（`docker compose stop`）`runserver` すると起動する？

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/hello/
curl -s -o /dev/null -w "%{http_code} %{redirect_url}\n" http://127.0.0.1:8000/admin/
```

```text
404
302 http://127.0.0.1:8000/admin/login/?next=/admin/
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / MySQL 8.4.11

<details><summary>答え</summary>

1. 404。ブラウザでは照合したパターン（`admin/`）の一覧が出る
2. 起動しない。起動時に DB へつなぎ、マイグレーションの状態を確かめるため

</details>

`docker compose start` で戻してください。

### 1-7. ✅ 想起チェック

1. `settings.py` が読まれるのはいつ？ `urls.py` は？
2. どれにも一致しないと何が返る？

<details><summary>答え</summary>

1. 起動時に1回 ／ リクエストごと
2. 404

</details>

### 1-8. 📇 まとめカード

この回で覚えることは1つだけ: **`settings.py` は起動時に1回、`urls.py` はリクエストごと。**

📒 用語集に追記: 設定モジュール / URLconf / 開発サーバ

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第1部 ステップ2` — カスタムユーザーモデル

---

## 第1部-2: カスタムユーザーモデル

**❓ この回の問い**: DB の接続先は決まった。最初の `migrate` の前に、済ませておくべきことは何か？

**作るもの**: 自分の `User` モデルを定義し、Django に「これを使え」と伝える
**重要度**: 🟡 読めればよい — 書くのは最初の1回。ただし忘れると戻せない
**前ステップとの接続**: 1-1 の `settings.py` に、アプリの登録と1行の指名を足す

### 2-0. このステップの初出

**Django / Ninja**: `AbstractUser`, `AUTH_USER_MODEL` / **Python**: クラスの継承, `pass`

> 🧒 **かみくだくと**: **モデル**は台帳（テーブル）の設計図。1-3 で詳しく扱う。

### 2-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

`accounts/models.py`（全文）

```python
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    # 今は AbstractUser の項目をそのまま使う。項目を足すときはここに書く
    pass
```

`config/settings.py`（差分。2か所）

```python
INSTALLED_APPS = [
    # （既存の django.contrib.* はそのまま）
    "accounts",  # 追加: accounts アプリを登録する
]

# 末尾に追加: 標準の auth.User の代わりに、accounts アプリの User を使う
AUTH_USER_MODEL = "accounts.User"
```

```bash
uv run python manage.py check
uv run python manage.py shell -c "from django.contrib.auth import get_user_model; print(get_user_model())"
```

```text
System check identified no issues (0 silenced).
6 objects imported automatically (use -v 2 for details).

<class 'accounts.models.User'>
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / MySQL 8.4.11（ruff・mypy も通過）

`get_user_model()` は「今使っているユーザーモデル」を返す関数です。**`migrate` はまだしません。**

### 2-2. 🔬 仕組み解剖

| | `AbstractUser` | `AUTH_USER_MODEL` |
| --- | --- | --- |
| 正式名称 | 抽象モデル `AbstractUser` | 設定 `AUTH_USER_MODEL` |
| いつ・誰が | 起動時に `username` などの項目を `User` に渡す。自分のテーブルは持たない | 起動時に読まれ、ユーザーの参照先を決める |
| TS での対応物 | `class User extends AbstractUser {}`（テーブル生成は対応物なし） | 対応物なし。DB の構造まで決める仕組みが無い |
| なぜこの設計 | 標準ユーザーの機能を丸ごと使える | 使う側が具体的なクラスに依存しない |
| 失敗すると | — | アプリ未登録なら `ImproperlyConfigured` |

```text
○ この教材の順番
  1-2  User を定義し、AUTH_USER_MODEL で指名
  1-3  初めての migrate → accounts_user ができ、ほかのテーブルがそれを参照する

✕ 逆の順番（試さないでください）
  ①  先に migrate            → auth_user ができ、admin などが auth_user を参照する
  ②  あとで User を差し替え  → migrate が InconsistentMigrationHistory で止まる
```

✅ 検証済み: ✕ の②は、別の DB で実際に起こしたエラー（全文は 2-6）

**なぜ最初でないと駄目か**: ほかのテーブルがユーザーを参照する先は、**最初の `migrate` で固定される**からです。

### 2-3. 🐍 Python注

> 🐍 `class User(AbstractUser):` は継承。TS の `class User extends AbstractUser` と同じ。
> 🐍 `pass` は「中身なし」を表す文。

### 2-4. 解説 — なぜこう設計するか

中身は標準と同じでも、差し替えておけば**あとから項目を足せます**。

🧠 Django の考え方: 変えられない決定は最初に済ませる。

### 2-5. 🏢 実務メモ

> 🏢 **実務メモ**: 新規プロジェクトでは、標準で足りてもカスタムユーザーモデルを作ることが公式に強く勧められている。
> 根拠: https://docs.djangoproject.com/en/5.2/topics/auth/customizing/#using-a-custom-user-model-when-starting-a-project

### 2-6. 🔮 予測 → 動作確認

1. `INSTALLED_APPS` から `"accounts"` を消して `check` すると？（試したら戻す）
2. 先に `migrate` してから差し替えていたら？（**試さない**）

```bash
uv run python manage.py check
```

```text
django.core.exceptions.ImproperlyConfigured: AUTH_USER_MODEL refers to model 'accounts.User' that has not been installed
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17（`"accounts"` を消した状態）

<details><summary>答え</summary>

1. 上の `ImproperlyConfigured`。指名先のアプリが登録されていない
2. 別の DB で実際に起こした結果:

```text
django.db.migrations.exceptions.InconsistentMigrationHistory: Migration admin.0001_initial is applied before its dependency accounts.0001_initial on database 'default'.
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / MySQL 8.4.11

直すには DB の作り直しが要ります。

</details>

### 2-7. ✅ 想起チェック

1. `AUTH_USER_MODEL` を最初の `migrate` より前に書くのはなぜ？

<details><summary>答え</summary>

1. 最初の `migrate` で、ほかのテーブルの参照先が固定されるから

</details>

### 2-8. 📇 まとめカード

この回で覚えることは1つだけ: **ユーザーモデルは、最初の `migrate` の前に差し替える。**

📒 用語集に追記: モデル / カスタムユーザーモデル / 抽象モデル

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第1部 ステップ3` — モデルを書く → マイグレーション

---

## 第1部-3: モデルを書く → マイグレーション

**❓ この回の問い**: 設計図（モデル）は、どうやって MySQL のテーブルになるのか？

**作るもの**: `Post`（記事）のモデルから `blog_post` テーブルを作る
**重要度**: 🔴 毎日使う — モデルを変えるたびに通る
**前ステップとの接続**: 1-2 で止めていた `migrate` を初めて実行する

### 3-0. このステップの初出

**Django / Ninja**: `models.Model` とフィールド, マイグレーション（`makemigrations` / `migrate`） / **Python**: キーワード引数, `def`・`self`・`-> str`

> 🧒 **かみくだくと**: **フィールド**は台帳の1列。**マイグレーション**は台帳を書き換える手続きで、SQL は Django が作る。

### 3-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

`blog/models.py`（全文）

```python
from django.db import models


class Post(models.Model):
    title = models.CharField(max_length=200)  # 短い文字列（上限200文字）
    body = models.TextField()  # 長い文章（上限なし）
    created_at = models.DateTimeField(auto_now_add=True)  # 作成時に自動で入る
    updated_at = models.DateTimeField(auto_now=True)  # 保存のたびに自動で更新

    def __str__(self) -> str:
        return self.title
```

`config/settings.py`（差分）: `INSTALLED_APPS` に `"blog",` を足す。

✅ 検証済み: Python 3.14.3 / Django 5.2.17（ruff・mypy も通過）

```bash
uv run python manage.py makemigrations       # 設計図の差分から、手続き書を作る
uv run python manage.py sqlmigrate blog 0001 # その手続き書が出す SQL を見る（実行はしない）
uv run python manage.py migrate              # 手続き書を DB に流す
```

```text
Migrations for 'blog':
  blog/migrations/0001_initial.py
    + Create model Post
Migrations for 'accounts':
  accounts/migrations/0001_initial.py
    + Create model User
```

```sql
CREATE TABLE `blog_post` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `title` varchar(200) NOT NULL, `body` longtext NOT NULL, `created_at` datetime(6) NOT NULL, `updated_at` datetime(6) NOT NULL);
```

```text
  Applying auth.0012_alter_user_first_name_max_length... OK
  Applying accounts.0001_initial... OK
  Applying admin.0001_initial... OK
  （中略）
  Applying blog.0001_initial... OK
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / MySQL 8.4.11

```bash
docker compose exec db mysql -udjango -pdjango blog -e "SHOW COLUMNS FROM blog_post; SHOW TABLES LIKE '%user';"
```

```text
Field       Type          Null  Key  Default  Extra
id          bigint        NO    PRI  NULL     auto_increment
title       varchar(200)  NO         NULL
body        longtext      NO         NULL
created_at  datetime(6)   NO         NULL
updated_at  datetime(6)   NO         NULL
Tables_in_blog (%user)
accounts_user
```

✅ 検証済み: MySQL 8.4.11（出力は列を揃えて表示）

> ✅ **回収**: 1-1 の未適用の警告はこれで消える。1-2 の通り、`accounts` は `admin` より先に適用され、`accounts_user` ができた。

> ⏭️ **後で回収**: `__str__`（1件を文字で表す方法）は 1-4 で効果を見る。

### 3-2. 🔬 仕組み解剖

| | `models.Model` とフィールド | マイグレーション |
| --- | --- | --- |
| 正式名称 | モデルとフィールド | `makemigrations` と `migrate` |
| いつ・誰が | 起動時に読まれる。DB には触らない | 前者はファイルを比べるだけ。後者は `django_migrations` を見て未実行分を流す |
| TS での対応物 | 対応物なし。TS の型は実行時に消える | 対応物なし（言語ではなく ORM の機能） |
| なぜこの設計 | 設計図を1か所に置き、SQL は DB ごとに作る | 変更を Git に残し、誰の DB でも再現できる |
| 失敗すると | `max_length` 忘れは `fields.E120` | 未実行ならテーブルが無い |

```text
blog/models.py（設計図）
   │  makemigrations … 前回の手続き書との差分を探す
   ▼
blog/migrations/0001_initial.py（台帳を書き換える手続き書）
   │  migrate … まだ実行していない手続き書だけを、順に流す
   ▼
MySQL: CREATE TABLE blog_post …  ＋  django_migrations に「実行済み」を記録
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / MySQL 8.4.11

見てほしいのは、**DB に触るのは `migrate` だけ**という点。

### 3-3. 🐍 Python注

> 🐍 `max_length=200` はキーワード引数（名前付きで値を渡す）。
> 🐍 `def __str__(self) -> str:` はメソッド。`self` は TS の `this`、`-> str` は戻り値の型。

### 3-4. 解説 — なぜこう設計するか

`id` 列は Django が自動で足します。書くのは記録したい項目だけです。

🧠 Django の考え方: 正しいのは設計図。DB はそれに合わせて作られる。

### 3-5. 🏢 実務メモ

> 🏢 **実務メモ**: `migrations/` のファイルは Git にコミットする。全員の DB を同じ形にするため。
> 根拠: https://docs.djangoproject.com/en/5.2/topics/migrations/

### 3-6. 🔮 予測 → 動作確認

1. `makemigrations` をもう一度実行すると、何が出る？
2. `created_at` の `Default` は `NULL`。作成時刻は誰が入れる？

```bash
uv run python manage.py makemigrations
```

```text
No changes detected
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17

<details><summary>答え</summary>

1. `No changes detected`
2. Django。`INSERT` 文に時刻を書き込む（1-6 で見る）

</details>

### 3-7. ✅ 想起チェック

1. `makemigrations` と `migrate`、DB に触るのはどっち？

<details><summary>答え</summary>

1. `migrate`

</details>

### 3-8. 📇 まとめカード

この回で覚えることは1つだけ: **`makemigrations` は手続き書を作り、`migrate` が DB に流す。**

📒 用語集に追記: フィールド / マイグレーション / マイグレーションファイル

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第1部 ステップ4` — 管理画面でデータを入れて見る

---

## 第1部-4: 管理画面でデータを入れて見る

**❓ この回の問い**: テーブルはできた。では、中にデータを入れて目で確かめるには？

**作るもの**: 管理画面から `Post` を2件登録し、MySQL で確かめる
**重要度**: 🟡 読めればよい — 登録の1行を書くだけ。以降の確認に使う
**前ステップとの接続**: 1-3 の `Post` を、管理画面に載せる

> **管理画面は学習対象ではありません。** データを見るための窓として使います。見た目の調整（カスタマイズ）は扱いません。

### 4-0. このステップの初出

**Django / Ninja**: `admin.site.register`, 管理画面 / **Python**: `from .models import`

### 4-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

`blog/admin.py`（全文）

```python
from django.contrib import admin

from .models import Post

# Post を管理画面に出す（見た目の調整はしない）
admin.site.register(Post)
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17（ruff・mypy も通過）

```bash
uv run python manage.py createsuperuser   # 管理画面に入れるユーザーを作る（対話式）
uv run python manage.py runserver
```

```text
Username: admin
Email address: admin@example.com
Password:
Password (again):
Superuser created successfully.
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / MySQL 8.4.11（検証は `--noinput` で実施）

ブラウザで `http://127.0.0.1:8000/admin/` を開き、ログインします。**Posts → 追加** から2件登録し、MySQL で中身を見ます。

```bash
docker compose exec db mysql -udjango -pdjango --default-character-set=utf8mb4 blog \
  -e "SELECT id, title, created_at FROM blog_post; SELECT username, LEFT(password, 30) FROM accounts_user;"
```

```text
id  title           created_at
1   はじめての投稿  2026-10-07 12:30:30.921057
2   二つ目の投稿    2026-10-07 12:30:30.946455
username  LEFT(password, 30)
admin     pbkdf2_sha256$1000000$1WFvz3fu
```

✅ 検証済み: MySQL 8.4.11（出力は列を揃えて表示）

> 🧒 **かみくだくと**: `--default-character-set=utf8mb4` は表示の文字コード。無いと日本語が `???` に見える。

> ✅ **回収**: 1-1 の `admin.site.urls` は、ここで登録した画面の URL 一式。1-3 の `__str__` は、一覧に出る名前になる（4-6）。

### 4-2. 🔬 仕組み解剖

| | `admin.site.register` | 管理画面 |
| --- | --- | --- |
| 正式名称 | `AdminSite.register` | Django admin |
| いつ・誰が | 起動時に各アプリの `admin.py` が自動で読まれ、登録簿に載る | リクエストごとに登録簿を見て、一覧・追加画面を作る |
| TS での対応物 | 対応物なし。モデルから画面を自動で作る標準が無い | 同左 |
| なぜこの設計 | 1行で CRUD の画面ができる | 確認用の API を作らずに済む |
| 失敗すると | 登録し忘れると一覧に出ない | 未ログインは `/admin/login/` へ 302 |

```text
【起動時】
  INSTALLED_APPS の各アプリの admin.py を読む
    └→ admin.site.register(Post) … 登録簿に Post を載せる

【リクエスト時】GET /admin/blog/post/
  urls.py の "admin/" → admin.site.urls → 登録簿から Post の一覧を作る
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17

見てほしいのは、**登録は起動時、画面づくりはリクエスト時**という分担です。

> ⏭️ **後で回収**: 管理画面のログインは「セッション認証」。第2部-6 で JWT と並べて比べる。

### 4-3. 🐍 Python注

> 🐍 `from .models import Post` の `.` は同じフォルダ。TS の `import { Post } from "./models"` と同じ。

### 4-4. 解説 — なぜこう設計するか

`accounts.User` は登録していないので画面に出ません。今は記事だけで足ります。

🧠 Django の考え方: よくある作業は、宣言1行で済むようにする。

### 4-5. 🏢 実務メモ

> 🏢 **実務メモ**: 管理画面は組織内の管理用。サイトの表側として作るものではない。
> 根拠: https://docs.djangoproject.com/en/5.2/ref/contrib/admin/

### 4-6. 🔮 予測 → 動作確認

1. `blog/models.py` の `__str__` を消すと、一覧の表示はどうなる？（試したら戻す）
2. `password` 列に、入力したパスワードはそのまま入っている？

<details><summary>答え</summary>

1. `Post object (1)` になる（検証済み）
2. 入っていない。`pbkdf2_sha256$...` は元に戻せない形（ハッシュ）に変えた値

</details>

### 4-7. ✅ 想起チェック

1. `admin.site.register(Post)` が実行されるのは、起動時？ リクエスト時？

<details><summary>答え</summary>

1. 起動時

</details>

### 4-8. 📇 まとめカード

この回で覚えることは1つだけ: **管理画面は、`admin.py` に1行書けば使える「データを見る窓」。**

📒 用語集に追記: 管理画面 / スーパーユーザー / ハッシュ

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第1部 ステップ5` — `JsonResponse` で一覧 GET を手書き

---

## 第1部-5: `JsonResponse` で一覧 GET を手書き

**❓ この回の問い**: データは管理画面で見えた。JSON で返すには何を書くのか？

**作るもの**: `GET /api/posts/` が記事の一覧を JSON で返す
**重要度**: 🔴 毎日使う — API の土台。1-7 で Ninja が肩代わりする部分
**前ステップとの接続**: 1-4 で入れた2件を JSON で取り出す

### 5-0. このステップの初出

**Django / Ninja**: `JsonResponse`（ビュー関数の戻り値）, `QuerySet` / **Python**: リスト内包表記

> 🧒 **かみくだくと**: **ビュー関数**は担当職員。リクエストを受け取り、返事を作る。
> **ORM** は台帳を引く職員。Python で書くと SQL にして MySQL に聞く。

### 5-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

`blog/views.py`（全文）

```python
from django.http import HttpRequest, JsonResponse

from .models import Post


def post_list(request: HttpRequest) -> JsonResponse:
    # 台帳（blog_post）から全件を取り出す。この時点ではまだ SQL は飛ばない
    posts = Post.objects.all()

    # 1件ずつ辞書に組み直す。ここで初めて SQL が1本飛ぶ
    data = [
        {
            "id": post.id,
            "title": post.title,
            "body": post.body,
            "created_at": post.created_at,
        }
        for post in posts
    ]

    # 辞書ではなくリストを返すので safe=False が要る
    return JsonResponse(data, safe=False)
```

`config/urls.py`（全文。冒頭の説明コメントは消してよい）

```python
from django.contrib import admin
from django.urls import path

from blog import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/posts/", views.post_list),  # 一覧 API
]
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17（ruff・mypy も通過）

```bash
uv run python manage.py runserver
# 別のターミナルで
curl -s http://127.0.0.1:8000/api/posts/ | uv run python -m json.tool --no-ensure-ascii
```

```json
[
    {
        "id": 1,
        "title": "はじめての投稿",
        "body": "本文です",
        "created_at": "2026-10-07T12:46:16.644Z"
    },
    {
        "id": 2,
        "title": "二つ目の投稿",
        "body": "本文です",
        "created_at": "2026-10-07T12:46:16.646Z"
    }
]
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / MySQL 8.4.11（`json.tool` は表示を整えるだけ）

SQL は shell（`uv run python manage.py shell`）で見られます。

```python
>>> from blog.models import Post
>>> qs = Post.objects.all()   # まだ SQL は飛ばない
>>> print(qs.query)           # 飛ぶ予定の SQL を表示するだけ
SELECT `blog_post`.`id`, `blog_post`.`title`, `blog_post`.`body`, `blog_post`.`created_at`, `blog_post`.`updated_at` FROM `blog_post`
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / MySQL 8.4.11

### 5-2. 🔬 仕組み解剖

| | `JsonResponse` | `QuerySet` |
| --- | --- | --- |
| 正式名称 | `django.http.JsonResponse` | `QuerySet`（`Post.objects` から作る） |
| いつ・誰が | ビューが返したあと JSON 文字列に変える。日時も変換する | 中身が要るとき（`for` など）に1回だけ SQL を出す |
| TS での対応物 | Express の `res.json(data)` | 対応物なし。TS の配列は作った時点で中身がある |
| なぜこの設計 | `Content-Type` も自動で付く | 条件を足してから1本の SQL にできる |
| 失敗すると | リストを `safe=False` なしで渡すと `TypeError`（500） | テーブルが無いと MySQL のエラー |

```text
GET /api/posts/（窓口に来た人）
  └→ config/urls.py（受付の案内表）… "api/posts/" に一致
       └→ blog/views.py の post_list（担当職員）
            ├→ Post.objects.all()（台帳を引く職員）… まだ何もしない
            ├→ for で回す → SELECT … FROM blog_post（MySQL）
            └→ JsonResponse(...) → JSON を返す（200）
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / MySQL 8.4.11

見てほしいのは、**SQL が飛ぶのは `all()` ではなく `for` の行**です。

### 5-3. 🐍 Python注

> 🐍 `[{...} for post in posts]` はリスト内包表記。TS の `posts.map((post) => ({...}))` と同じ。

### 5-4. 解説 — なぜこう設計するか

ビューは「引く → 組み直す → 返す」の3段です。何を返すか（`updated_at` は返さない）もここで決まります。

🧠 Django の考え方: SQL は必要になるまで出さない（遅延評価）。
根拠: https://docs.djangoproject.com/en/5.2/topics/db/queries/#querysets-are-lazy

### 5-5. 🔮 予測 → 動作確認

1. `qs = Post.objects.all()` の時点で SQL は何本？ `for` で回したあとは？
2. 生の `curl` では、日本語はどう見える？
3. `safe=False` を消して叩くと？（試したら戻す）

```bash
curl -s http://127.0.0.1:8000/api/posts/
```

```text
[{"id": 1, "title": "\u306f\u3058\u3081\u3066\u306e\u6295\u7a3f", ...
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / MySQL 8.4.11

<details><summary>答え</summary>

1. 0本 → 1本（接続直後の準備用 SQL を除く）
2. `\u306f…` になる。正しい JSON で、受け取る側で日本語に戻る
3. 500。ログに `TypeError: In order to allow non-dict objects to be serialized set the safe parameter to False.`

</details>

### 5-6. ✅ 想起チェック

1. `Post.objects.all()` と書いた行で、SQL は飛ぶ？

<details><summary>答え</summary>

1. 飛ばない

</details>

### 5-7. 📇 まとめカード

この回で覚えることは1つだけ: **`QuerySet` は使うまで SQL を出さない。ビューは組み直して `JsonResponse` で返す。**

📒 用語集に追記: ビュー関数 / ORM / QuerySet / 遅延評価

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第1部 ステップ6` — `JsonResponse` で POST を手書き

---

## 第1部-6: `JsonResponse` で POST を手書き

**❓ この回の問い**: GET は書けた。送られた JSON を保存する前に、何を確かめるのか？

**作るもの**: `POST /api/posts/` で記事を作る。誤りには 400 で理由を返す
**重要度**: 🔴 毎日使う — 1-7 で Ninja が肩代わりする中身
**前ステップとの接続**: 1-5 の `post_list` に POST を足す

### 6-0. このステップの初出

**Django / Ninja**: `csrf_exempt`, `objects.create()` / **Python**: `@`（デコレータ）, `try`/`except`, `isinstance`

> 🧒 **かみくだくと**: **CSRF** は、別のサイトから勝手に送信させる攻撃。
> Django は、POST に「正規の画面から来た印」が無いと 403 で止める。

### 6-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

`blog/views.py`（全文。1-5 の内容も含む）

```python
import json

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Post


def post_to_dict(post: Post) -> dict[str, object]:
    # 1件の Post を、返す形（辞書）に組み直す
    return {
        "id": post.id,
        "title": post.title,
        "body": post.body,
        "created_at": post.created_at,
    }


@csrf_exempt  # このビューだけ CSRF の検査を外す（理由は 6-2）
def post_list(request: HttpRequest) -> JsonResponse:
    if request.method == "GET":
        data = [post_to_dict(post) for post in Post.objects.all()]
        return JsonResponse(data, safe=False)

    if request.method == "POST":
        return create_post(request)

    return JsonResponse({"detail": "許可されていないメソッドです"}, status=405)


def create_post(request: HttpRequest) -> JsonResponse:
    # ① 本文を JSON として読む
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"detail": "JSON として読めません"}, status=400)
    if not isinstance(payload, dict):
        return JsonResponse({"detail": "JSON はオブジェクトで送ってください"}, status=400)

    # ② 必須チェックと型チェック。エラーは項目ごとに集める
    errors: dict[str, str] = {}
    title = payload.get("title")
    body = payload.get("body")

    if title is None:
        errors["title"] = "必須です"
    elif not isinstance(title, str):
        errors["title"] = "文字列で送ってください"
    elif len(title) > 200:
        errors["title"] = "200文字以内にしてください"

    if body is None:
        errors["body"] = "必須です"
    elif not isinstance(body, str):
        errors["body"] = "文字列で送ってください"

    # isinstance も条件に入れると、この先で両方が str だと mypy にも伝わる
    if errors or not isinstance(title, str) or not isinstance(body, str):
        return JsonResponse({"errors": errors}, status=400)

    # ③ 保存して、作ったものを 201 で返す
    post = Post.objects.create(title=title, body=body)
    return JsonResponse(post_to_dict(post), status=201)
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / MySQL 8.4.11（ruff・mypy も通過）

```bash
curl -s -w '\n%{http_code}\n' -X POST http://127.0.0.1:8000/api/posts/ \
  -H 'Content-Type: application/json' -d '{"title": "三つ目の投稿", "body": "POST で作った"}'
curl -s -w '\n%{http_code}\n' -X POST http://127.0.0.1:8000/api/posts/ \
  -H 'Content-Type: application/json' -d '{"title": 123}'
```

```text
{"id": 3, "title": "三つ目の投稿", "body": "POST で作った", "created_at": "2026-10-07T23:32:07.327Z"}
201
{"errors": {"title": "文字列で送ってください", "body": "必須です"}}
400
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / MySQL 8.4.11（日本語は `\u…` を読める形に直して表示。`id` は手元のデータ件数で変わる）

`create()` が出す SQL（shell の `connection.queries` で表示）:

```sql
INSERT INTO `blog_post` (`title`, `body`, `created_at`, `updated_at`) VALUES ('shell から', 'b', '2026-10-07 23:32:35.603592', '2026-10-07 23:32:35.603607')
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / MySQL 8.4.11

> ✅ **回収（1-3）**: 作成時刻は Django が `INSERT` に書き込む。

### 6-2. 🔬 仕組み解剖

| | `csrf_exempt` | `objects.create()` |
| --- | --- | --- |
| 正式名称 | `csrf_exempt` | `QuerySet.create()` |
| いつ・誰が | 起動時に関数へ印を付ける。リクエスト時、CSRF 検査がその印を見て通す | 呼んだ瞬間に `INSERT` を出す（遅延しない） |
| TS での対応物 | TS のデコレータ（`@`）と同じ形 | 対応物なし（ORM の機能） |
| なぜこの設計 | 検査は全体に掛け、外すときは明示する | 作成と保存を1行で |
| 失敗すると | 外さないと 403 | 値は検査しない。長すぎると MySQL の `DataError (1406)` |

```text
POST /api/posts/
  ├─ ① JSON として読めない             → 400  {"detail": "…"}
  ├─ ② 必須・型・長さのどれかが違う    → 400  {"errors": {項目: 理由}}
  └─ 問題なし → Post.objects.create()  → 201  作った記事
```

✅ 検証済み: 3つの分かれ道すべてを curl で確認

見てほしいのは、**保存前の関門2つを自分で書いている**ことです。

### 6-3. 🐍 Python注

> 🐍 `@csrf_exempt` はデコレータ。直下の関数を包んで機能を足す。
> 🐍 `try`/`except` は TS の `try`/`catch`。`isinstance(x, str)` は `typeof x === "string"`。

### 6-4. 解説 — なぜこう設計するか

`create_post` は約30行。ほとんどが値を信用しないための関門です。

🧠 Django の考え方: 外から来た値は保存前に確かめる。

### 6-5. 🔓 教材用の簡略化

> 🔓 **教材用の簡略化**: `csrf_exempt` で検査を外している。第1部は誰でも書ける API なので、失うものが無い。
> **本番では**: Cookie でログインする API なら外さない。JWT との違いは第2部-6 で表にする。
> 根拠: https://docs.djangoproject.com/en/5.2/ref/csrf/#how-it-works

### 6-6. 🔮 予測 → 動作確認

1. `csrf_exempt` が無いと、POST で何が返る？
2. 201文字の `title` を送ると？
3. `PUT` では？

<details><summary>答え</summary>

1. 403 `CSRF verification failed.`（検証済み）
2. 400 `{"errors": {"title": "200文字以内にしてください"}}`
3. 405 `{"detail": "許可されていないメソッドです"}`

</details>

### 6-7. ✅ 想起チェック

1. 保存の前に確かめていることを2つ挙げると？

<details><summary>答え</summary>

1. JSON として読めるか。項目・型・長さが正しいか

</details>

### 6-8. 📇 まとめカード

この回で覚えることは1つだけ: **手書きの API では、受け取った値の検査を全部自分で書く。**

📒 用語集に追記: CSRF / デコレータ / バリデーション

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第1部 ステップ7` — 同じものを Ninja で書き直す

---

## 第1部-7: 同じものを Ninja で書き直す

**❓ この回の問い**: 1-6 の検査は約30行。もっと短く確実に書けないか？

**作るもの**: 一覧と作成を Ninja で書き直す（手書き版は `/manual/posts/` へ）
**重要度**: 🔴 毎日使う — 以降の API はすべてこの形
**前ステップとの接続**: 1-6 の検査を Ninja に任せる

### 7-0. このステップの初出

**Django / Ninja**: `NinjaAPI` とデコレータ, `Schema` / **Python**: クラス属性の型注釈

> 🧒 **かみくだくと**: **Django Ninja** は Django の上の薄い層。**Pydantic** は型注釈で値を検査する部品で、Ninja の中で動く。

### 7-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

`config/api.py`（新規・全文）

```python
from django.http import HttpRequest
from ninja import Field, NinjaAPI, Schema

from blog.models import Post
from blog.views import post_to_dict  # 返す形は 1-6 の手書き版を使い回す

api = NinjaAPI()


class PostIn(Schema):
    # 申請書の書式: 何を・どの型で・どんな条件で受け取るか
    title: str = Field(max_length=200)
    body: str


@api.get("/posts")
def list_posts(request: HttpRequest) -> list[dict[str, object]]:
    return [post_to_dict(post) for post in Post.objects.all()]


@api.post("/posts")
def create_post(request: HttpRequest, payload: PostIn) -> dict[str, object]:
    # ここに来た時点で、payload は検査済み（title も body も str）
    post = Post.objects.create(title=payload.title, body=payload.body)
    return post_to_dict(post)
```

`config/urls.py`（全文）

```python
from django.contrib import admin
from django.urls import path

from blog import views
from config.api import api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("manual/posts/", views.post_list),  # 1-5・1-6 の手書き版（比較用に残す）
    path("api/", api.urls),  # Ninja の API 一式
]
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / django-ninja 1.7.1 / MySQL 8.4.11（ruff・mypy も通過）

```bash
curl -s -w '\n%{http_code}\n' -X POST http://127.0.0.1:8000/api/posts \
  -H 'Content-Type: application/json' -d '{"title": "Ninja で作った", "body": "b"}'
curl -s -w '\n%{http_code}\n' -X POST http://127.0.0.1:8000/api/posts \
  -H 'Content-Type: application/json' -d '{"title": 123}'
```

```text
{"id": 4, "title": "Ninja で作った", "body": "b", "created_at": "2026-10-08T12:33:18.675Z"}
200
{"detail": [{"type": "string_type", "loc": ["body", "payload", "title"], "msg": "Input should be a valid string"}, {"type": "missing", "loc": ["body", "payload", "body"], "msg": "Field required"}]}
422
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / django-ninja 1.7.1 / MySQL 8.4.11（日本語は読める形に直して表示。`id` は手元の件数で変わる）

**手書き版との差分** — `create_post` は 28行 → 5行（空行を除く）

| 1-6 の手書き | 1-7 の Ninja | 肩代わり |
| --- | --- | --- |
| `request.method` の分岐と 405 | `@api.get` / `@api.post` | Ninja（405） |
| `json.loads` と `try`/`except` | 書かない | Ninja（400） |
| 必須・型・長さの `if` の山 | `title: str = Field(max_length=200)` | Pydantic（違えば 422） |
| エラーの形を組む | 書かない | Ninja（`{"detail": [...]}`） |
| `@csrf_exempt` | 書かない | Ninja（Cookie 認証なしなら検査不要） |

根拠（CSRF）: https://django-ninja.dev/guide/csrf/

### 7-2. 🔬 仕組み解剖

| | `NinjaAPI` とデコレータ | `Schema` |
| --- | --- | --- |
| 正式名称 | `NinjaAPI` と `@api.get` など | `ninja.Schema`（Pydantic） |
| いつ・誰が | 起動時に関数を登録し、URL 一式を作る | 関数を呼ぶ**前に**毎回検査する |
| TS での対応物 | Express の `app.get` など | zod の `z.object({...})` |
| なぜこの設計 | メソッドごとに関数を分けられる | 型注釈で検査が済む |
| 失敗すると | 405 | 422（項目ごとの理由付き） |

```text
POST /api/posts（窓口に来た人）
  └→ Ninja が本文を JSON として読む           … 読めなければ 400
       └→ Pydantic が PostIn の書式で検査     … 合わなければ 422
            └→ create_post(request, payload)  … ここから自分のコード
```

✅ 検証済み: 400・422・200 のすべてを curl で確認

見てほしいのは、**検査が関数の外に移った**ことです。

### 7-3. 🐍 Python注

> 🐍 `title: str = Field(...)` は型付きのクラス属性。TS の `title: string` に条件を足した形。
> 🐍 Python の型注釈は実行時にも残る（TS は消える）。Ninja はそれで検査する。

### 7-4. 解説 — なぜこう設計するか

保存は Django のまま。Ninja が足したのは検査だけです。

🧠 Django の考え方: 書式チェックは Ninja、台帳は Django。

### 7-5. 🔮 予測 → 動作確認

1. 作成成功のステータスは 201？ 200？
2. `/api/posts/`（末尾にスラッシュ）を叩くと？

<details><summary>答え</summary>

1. 200。201 には出力の形の宣言が要る（1-8）
2. 404。URL は `posts` なので一致しない

</details>

### 7-6. ✅ 想起チェック

1. `payload: PostIn` と書くと、関数が呼ばれる前に何が起きる？

<details><summary>答え</summary>

1. JSON が読まれ、`PostIn` の書式で検査される

</details>

### 7-7. 📇 まとめカード

この回で覚えることは1つだけ: **`Schema` に書式を宣言すれば、検査は関数の前に Ninja が済ませる。**

📒 用語集に追記: Django Ninja / Pydantic / スキーマ

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第1部 ステップ8` — Swagger UI と OpenAPI

---

## 第1部-8: Swagger UI と OpenAPI

**❓ この回の問い**: 1-7 は入力だけ宣言した。出力も宣言すると何が手に入るのか？

**作るもの**: `PostOut` を宣言して作成を 201 にし、`/api/docs` から試す
**重要度**: 🔴 毎日使う — 以降の API は入出力を宣言する
**前ステップとの接続**: 1-7 の `post_to_dict` を宣言に置き換える

### 8-0. このステップの初出

**Django / Ninja**: OpenAPI の自動生成, `response=`（`Status` で返す） / **Python**: `list[...]`

> 🧒 **かみくだくと**: **OpenAPI** は API の説明書の決まった書き方。**Swagger UI** はそれを画面にし、ブラウザから試せる道具。

### 8-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

`config/api.py`（全文）

```python
from datetime import datetime

from django.http import HttpRequest
from ninja import Field, NinjaAPI, Schema, Status

from blog.models import Post

api = NinjaAPI()


class PostIn(Schema):
    # 受け取る書式（入力）
    title: str = Field(max_length=200)
    body: str


class PostOut(Schema):
    # 返す書式（出力）。ここに無い項目は返さない
    id: int
    title: str
    body: str
    created_at: datetime


@api.get("/posts", response=list[PostOut])
def list_posts(request: HttpRequest):  # 戻り値の形は response= で宣言する
    return Post.objects.all()


@api.post("/posts", response={201: PostOut})
def create_post(request: HttpRequest, payload: PostIn):
    post = Post.objects.create(title=payload.title, body=payload.body)
    return Status(201, post)  # ステータスと中身を一緒に返す
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / django-ninja 1.7.1 / MySQL 8.4.11（ruff・mypy も通過）

`http://127.0.0.1:8000/api/docs` を開き、**POST /api/posts → Try it out** に JSON を書いて **Execute** を押します。

```text
Server response
Code: 201
Response body:
{
  "id": 2,
  "title": "Swagger UI から",
  "body": "b",
  "created_at": "2026-10-08T12:56:22.547Z"
}
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / django-ninja 1.7.1 / MySQL 8.4.11（ブラウザで実際に操作した結果）

説明書は `/api/openapi.json` にあります。

```json
"PostIn": {
  "properties": {
    "title": {"maxLength": 200, "title": "Title", "type": "string"},
    "body": {"title": "Body", "type": "string"}
  },
  "required": ["title", "body"]
}
```

✅ 検証済み: django-ninja 1.7.1（OpenAPI 3.1.0。`POST /api/posts` の応答は `201` と記載される）

> ✅ **回収（1-7）**: 出力を `{201: PostOut}` と宣言したので、作成が 201 になった。

> 💡補足: 古い資料の `return 201, post` は非推奨。
> 根拠: https://django-ninja.dev/guide/responses/

### 8-2. 🔬 仕組み解剖

| | OpenAPI の自動生成 | `response=` |
| --- | --- | --- |
| 正式名称 | OpenAPI 3.1 の説明書と Swagger UI | 出力スキーマの宣言 |
| いつ・誰が | `openapi.json` を開いたとき、関数と `Schema` から組み立てる | 関数が返したあと、`PostOut` の形に整える |
| TS での対応物 | 対応物なし。TS の型は実行時に消える | 同左 |
| なぜこの設計 | コードと説明書がずれない | 返す項目を宣言で決める |
| 失敗すると | — | 形が合わないと 500（`ValidationError`） |

```text
config/api.py の宣言（PostIn / PostOut / @api.post）
  ├→ リクエスト時: PostIn で検査 → 関数 → PostOut で整形
  └→ /api/openapi.json: 同じ宣言から説明書を作る → /api/docs が画面にする
```

✅ 検証済み: django-ninja 1.7.1

見てほしいのは、**1つの宣言が検査にも説明書にもなる**点です。

### 8-3. 🐍 Python注

> 🐍 `Status(201, post)` は TS の `new Status(201, post)`。Python は `new` を書かない。
> 🐍 `list[PostOut]` は「`PostOut` のリスト」という型。TS の `PostOut[]`。

### 8-4. 解説 — なぜこう設計するか

関数は `Post` を返し、出す項目は `PostOut` が決めます。

🧠 Django の考え方: 台帳の形（モデル）と窓口で見せる形（スキーマ）を分ける。

### 8-5. 🔓 教材用の簡略化

> 🔓 **教材用の簡略化**: `/api/docs` を誰でも見られる状態にしている。
> **本番では**: `NinjaAPI(docs_decorator=staff_member_required)` などで、見られる人を絞る。
> 根拠: https://django-ninja.dev/guide/openapi/#protecting-the-docs

### 8-6. 🔮 予測 → 動作確認

1. モデルにある `updated_at` は、一覧の応答に入る？
2. `list_posts` が `[{"id": 1, "title": "t"}]` を返したら？

<details><summary>答え</summary>

1. 入らない（`PostOut` に無い）
2. 500。ログに `ValidationError`（`Field required` が2つ）

</details>

### 8-7. ✅ 想起チェック

1. `response={201: PostOut}` の使い道を2つ挙げると？

<details><summary>答え</summary>

1. 応答を整えること。説明書に書かれること

</details>

### 8-8. 📇 まとめカード

この回で覚えることは1つだけ: **入出力を宣言すれば、検査も説明書も Ninja が作る。**

📒 用語集に追記: OpenAPI / Swagger UI / Status

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第1部 ステップ9` — 1件取得

---

## 第1部-9: 1件取得

**❓ この回の問い**: 一覧と作成はできた。URL で「この1件」を指して、無ければ 404 を返すには？

**作るもの**: `GET /api/posts/{post_id}` が1件を返す。無ければ 404
**重要度**: 🔴 毎日使う — 詳細・更新・削除のすべてで使う形
**前ステップとの接続**: 1-8 の `config/api.py` に関数を1つ足す

### 9-0. このステップの初出

**Django / Ninja**: パスパラメータ, `get_object_or_404` / **Python**: なし

> 🧒 **かみくだくと**: **パスパラメータ**は、URL の一部を値として受け取る仕組み。`/posts/3` の `3` を引数にする。

### 9-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

`config/api.py`（差分。import を1行、末尾に関数を1つ足す）

```python
from django.shortcuts import get_object_or_404  # import 群に足す

# （中略）


@api.get("/posts/{post_id}", response=PostOut)
def get_post(request: HttpRequest, post_id: int):
    # {post_id} の部分が、同じ名前の引数に int で渡される
    return get_object_or_404(Post, id=post_id)  # 無ければ 404
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / django-ninja 1.7.1（ruff・mypy も通過）

```bash
curl -s -w '\n%{http_code}\n' http://127.0.0.1:8000/api/posts/1
curl -s -w '\n%{http_code}\n' http://127.0.0.1:8000/api/posts/999
```

```text
{"id": 1, "title": "はじめての投稿", "body": "本文です", "created_at": "2026-10-08T13:11:10.075Z"}
200
{"detail": "Not Found: No Post matches the given query."}
404
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / django-ninja 1.7.1 / MySQL 8.4.11（日本語は読める形に直して表示）

発行される SQL（shell で確認）:

```sql
SELECT `blog_post`.`id`, `blog_post`.`title`, `blog_post`.`body`, `blog_post`.`created_at`, `blog_post`.`updated_at` FROM `blog_post` WHERE `blog_post`.`id` = 1 LIMIT 21
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / MySQL 8.4.11

### 9-2. 🔬 仕組み解剖

| | パスパラメータ | `get_object_or_404` |
| --- | --- | --- |
| 正式名称 | Path parameters（`{post_id}`） | ショートカット関数 `get_object_or_404` |
| いつ・誰が | リクエストごとに URL から取り出し、`int` で検査する | 1件を探す SQL を出す。無ければ `Http404` を投げる |
| TS での対応物 | Express の `/posts/:id` と `req.params.id` | 対応物なし（ORM の機能） |
| なぜこの設計 | 型注釈で数字の検査まで済む | 「探す → 無ければ 404」を1行に |
| 失敗すると | 数字でなければ 422 | 無ければ 404 |

```text
GET /api/posts/999
  └→ Ninja: "999" を int に変換 … 数字でなければ 422
       └→ get_object_or_404(Post, id=999)
            ├─ 見つかった  → PostOut で整形 → 200
            └─ 無い        → Http404 → Ninja が {"detail": …} → 404
```

✅ 検証済み: 200・404・422 のすべてを curl で確認

見てほしいのは、**404 を返すコードを自分では書いていない**ことです。

### 9-3. 🐍 Python注

（この回は新しい文法なし）

### 9-4. 解説 — なぜこう設計するか

SQL の `LIMIT 21` は、1件のはずが複数あったときに気づくための上限です。

🧠 Django の考え方: 「よくある失敗」は、決まった形で返す近道を用意する。

### 9-5. 🔓 教材用の簡略化

> 🔓 **教材用の簡略化**: 404 の本文に `No Post matches the given query.` という内部の説明が出ている。`DEBUG = True` だから。
> **本番では**: `DEBUG = False` なら `{"detail": "Not Found"}` だけになる。
> 根拠: https://github.com/vitalik/django-ninja/blob/master/ninja/errors.py （`_default_404`）

### 9-6. 🔮 予測 → 動作確認

1. `/api/posts/abc` を叩くと、404？ 422？
2. `/api/posts/1/`（末尾にスラッシュ）では？
3. URL を `"/posts/{int:post_id}"` に変えると、`/api/posts/abc` は？（試したら戻す）

<details><summary>答え</summary>

1. 422。`Input should be a valid integer`（URL は一致し、型の検査で落ちる）
2. 404。URL が一致しない
3. 404。`int:` は Django の型付き URL。数字以外は URL が一致しなくなる（検証済み）

</details>

### 9-7. ✅ 想起チェック

1. `get_object_or_404` は、見つからないとき何を投げる？ それを 404 に変えるのは誰？

<details><summary>答え</summary>

1. `Http404` を投げる。Ninja が 404 の JSON に変える

</details>

### 9-8. 📇 まとめカード

この回で覚えることは1つだけ: **1件取得は `{post_id}` と `get_object_or_404` の組で書く。**

📒 用語集に追記: パスパラメータ / 404

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第1部 ステップ10` — 更新

---

## 第1部-10: 更新

**❓ この回の問い**: 1件を指せた。その「送った項目だけ」を変えるには？

**作るもの**: `PATCH /api/posts/{post_id}` で、送った項目だけを変える
**重要度**: 🔴 毎日使う — 更新 API の基本形
**前ステップとの接続**: 1-9 で取った1件を書き換えて保存する

### 10-0. このステップの初出

**Django / Ninja**: `model_dump(exclude_unset=True)`, `save()` / **Python**: `str | None`, `for ... in ...items()`, `setattr`

> 🧒 **かみくだくと**: **PATCH** は一部だけ変える HTTP メソッド。全部を送り直す `PUT` と区別する。

### 10-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

`config/api.py`（差分。`PostOut` の上に書式を1つ、末尾に関数を1つ足す）

```python
class PostPatch(Schema):
    # 更新の書式。どの項目も省略してよい（省略した項目は変えない）
    title: str | None = Field(default=None, max_length=200)
    body: str | None = None


# （中略）


@api.patch("/posts/{post_id}", response=PostOut)
def update_post(request: HttpRequest, post_id: int, payload: PostPatch):
    post = get_object_or_404(Post, id=post_id)
    # 送られてきた項目だけを取り出す（省略した項目・null の項目は入らない）
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    for name, value in changes.items():
        setattr(post, name, value)  # post.title = value と同じ
    post.save()
    return post
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / django-ninja 1.7.1（ruff・mypy も通過）

```bash
curl -s -X PATCH http://127.0.0.1:8000/api/posts/1 \
  -H 'Content-Type: application/json' -d '{"title": "題名だけ変えた"}'
```

```text
{"id": 1, "title": "題名だけ変えた", "body": "本文です", "created_at": "2026-10-11T11:19:47.685Z"}
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / django-ninja 1.7.1 / MySQL 8.4.11（`body` はそのまま。MySQL の `updated_at` は更新された）

`save()` が出す SQL（shell で確認）:

```sql
UPDATE `blog_post` SET `title` = 'shell で変更', `body` = '本文です', `created_at` = '2026-10-11 11:19:47.685476', `updated_at` = '2026-10-11 11:19:54.141047' WHERE `blog_post`.`id` = 1
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / MySQL 8.4.11

### 10-2. 🔬 仕組み解剖

| | `model_dump(exclude_unset=True)` | `save()` |
| --- | --- | --- |
| 正式名称 | Pydantic の `model_dump` | `Model.save()` |
| いつ・誰が | 送られた項目だけの辞書を作る | 呼んだ瞬間に SQL を出す（`id` があるので `UPDATE`） |
| TS での対応物 | 対応物なし | 対応物なし（ORM の機能） |
| なぜこの設計 | 「省略 = 変えない」を表せる | 新規か更新かを Django が判断する |
| 失敗すると | `null` を除かないと 500 | 変えていない列も書き直す |

```text
{"title": "題名だけ変えた"}
  └→ PostPatch で検査 … 型・長さが違えば 422
       └→ model_dump(...) → {"title": "題名だけ変えた"}（body は入らない）
            └→ setattr で post に書き込む → save() → UPDATE → 200
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / django-ninja 1.7.1 / MySQL 8.4.11

見てほしいのは、**送らなかった `body` が辞書に入らない**点です。

### 10-3. 🐍 Python注

> 🐍 `str | None` は「文字列か None」。TS の `string | null`。
> 🐍 `for name, value in changes.items():` は辞書の名前と値を1組ずつ取り出す。`setattr` は `post[name] = value` に近い。

### 10-4. 解説 — なぜこう設計するか

`exclude_none=True` で、`null` は「変えない」扱いにしました。`title` の列は空にできないためです。

🧠 Django の考え方: 変える項目はスキーマで絞り、保存は `save()` に任せる。

### 10-5. 🏢 実務メモ

> 🏢 **実務メモ**: 書き直す列を絞るなら `save(update_fields=[...])`。`auto_now` の列も名前に入れる。
> 根拠: https://docs.djangoproject.com/en/5.2/ref/models/instances/#specifying-which-fields-to-save

```sql
-- p.save(update_fields=["title", "updated_at"]) の SQL
UPDATE `blog_post` SET `title` = 'u', `updated_at` = '2026-10-11 11:21:01.202272' WHERE `blog_post`.`id` = 1
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / MySQL 8.4.11

### 10-6. 🔮 予測 → 動作確認

1. `{}`（空）を送ると？
2. `{"title": null}` を送ると？
3. `exclude_none=True` を消して `{"title": null}` を送ると？（試したら戻す）

<details><summary>答え</summary>

1. 200。何も変わらない
2. 200。`exclude_none` で除かれ、何も変わらない
3. 500。`IntegrityError: (1048, "Column 'title' cannot be null")`（検証済み）

</details>

### 10-7. ✅ 想起チェック

1. 「送られた項目だけ」を取り出す指定は？

<details><summary>答え</summary>

1. `model_dump(exclude_unset=True)`

</details>

### 10-8. 📇 まとめカード

この回で覚えることは1つだけ: **PATCH は「送られた項目だけ」を `model_dump(exclude_unset=True)` で取り出す。**

📒 用語集に追記: PATCH / PUT

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第1部 ステップ11` — 削除

---

## 第1部-11: 削除

**❓ この回の問い**: 作成・取得・更新ができた。最後の削除は、成功したとき何を返せばよいのか？

**作るもの**: `DELETE /api/posts/{post_id}` が 204（中身なし）を返す
**重要度**: 🔴 毎日使う — CRUD の最後の1つ
**前ステップとの接続**: 1-10 と同じく1件を取り、今度は消す

### 11-0. このステップの初出

**Django / Ninja**: `delete()`, 204 と `response={204: None}` / **Python**: `None`

> 🧒 **かみくだくと**: **204** は「成功した。返す中身は無い」というステータス。削除のように、返すものが無い成功で使う。

### 11-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

`config/api.py`（差分。末尾に関数を1つ足す）

```python
@api.delete("/posts/{post_id}", response={204: None})
def delete_post(request: HttpRequest, post_id: int):
    post = get_object_or_404(Post, id=post_id)
    post.delete()
    return Status(204, None)  # 204 は「成功。返す中身は無い」
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / django-ninja 1.7.1（ruff・mypy も通過）

```bash
curl -s -i -X DELETE http://127.0.0.1:8000/api/posts/1
curl -s -w '\n%{http_code}\n' -X DELETE http://127.0.0.1:8000/api/posts/1
```

```text
HTTP/1.1 204 No Content
Content-Length: 0
（以下ヘッダーは略）
{"detail": "Not Found: No Post matches the given query."}
404
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / django-ninja 1.7.1 / MySQL 8.4.11（1回目は 204、同じ id の2回目は 404）

発行される SQL（shell で確認）:

```sql
SELECT `blog_post`.`id`, `blog_post`.`title`, `blog_post`.`body`, `blog_post`.`created_at`, `blog_post`.`updated_at` FROM `blog_post` WHERE `blog_post`.`id` = 1 LIMIT 21
DELETE FROM `blog_post` WHERE `blog_post`.`id` IN (1)
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / MySQL 8.4.11

### 11-2. 🔬 仕組み解剖

| | `delete()` | `response={204: None}` |
| --- | --- | --- |
| 正式名称 | `Model.delete()` | 中身の無い応答の宣言 |
| いつ・誰が | 呼んだ瞬間に `DELETE` を出す。戻り値は `(1, {'blog.Post': 1})`（消えた件数） | 関数が `Status(204, None)` を返すと、Ninja が本文の無い応答にする |
| TS での対応物 | 対応物なし（ORM の機能） | Express の `res.status(204).end()` |
| なぜこの設計 | 関連するデータも、まとめて消せる作りになっている（第2部で見る） | 「消えたものは返せない」を宣言で表す |
| 失敗すると | — | 宣言に無いステータスを返すと 500（1-7 で見た） |

```text
DELETE /api/posts/1
  └→ get_object_or_404 … SELECT。無ければ 404
       └→ post.delete() … DELETE
            └→ return Status(204, None) → 本文なしの 204
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / MySQL 8.4.11

見てほしいのは、**SQL が2本（探す・消す）出ている**ことです。

### 11-3. 🐍 Python注

> 🐍 `None` は「値が無い」を表す。TS の `null` に当たる。

### 11-4. 解説 — なぜこう設計するか

これで `/api/posts` の CRUD（作成・一覧・取得・更新・削除）がそろいました。どの操作も「宣言（スキーマ）＋ ORM 1〜2行」の同じ形です。

🧠 Django の考え方: 同じ形を繰り返せるように、宣言と ORM で書く。

### 11-5. 🏢 実務メモ

> 🏢 **実務メモ**: 消すだけなら `Post.objects.filter(id=post_id).delete()` でも書ける。探す SQL が要らず、戻り値の件数が 0 なら「無かった」と分かる。
> 根拠: https://docs.djangoproject.com/en/5.2/topics/db/queries/#deleting-objects

```sql
-- Post.objects.filter(id=2).delete() の SQL（戻り値は (1, {'blog.Post': 1})）
BEGIN
DELETE FROM `blog_post` WHERE `blog_post`.`id` = 2
COMMIT
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / MySQL 8.4.11

### 11-6. 🔮 予測 → 動作確認

1. 同じ id を2回 `DELETE` すると、2回目は？
2. 204 の応答の本文は？

<details><summary>答え</summary>

1. 404。もう無いので `get_object_or_404` で止まる
2. 空（`Content-Length: 0`）

</details>

### 11-7. ✅ 想起チェック

1. 削除の成功で 200 ではなく 204 を返すのはなぜ？

<details><summary>答え</summary>

1. 返す中身が無いから。204 は「成功・中身なし」を表す

</details>

### 11-8. 📇 まとめカード

この回で覚えることは1つだけ: **削除は `delete()` で消し、中身の無い成功として 204 を返す。**

📒 用語集に追記: 204 / CRUD

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第1部 ステップ12` — テストで固定する
