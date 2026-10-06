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
