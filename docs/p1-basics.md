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
