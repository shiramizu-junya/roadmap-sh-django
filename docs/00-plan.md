# 00. 学習計画（M0）

Django + Django Ninja で REST API を作る教材の、全体の地図です。
本編はまだ書きません。ここでは「どこまで行くか」「何をどの順で学ぶか」だけを決めます。

> この教材は、1周目で全部分かるようには作られていません。
> 分からない箇所には `# TODO: わからん` と残して、先に進んでください。

---

## 1. 各部の到達点

| 部 | 終えたとき、できること | ステップ |
| --- | --- | --- |
| **第1部** | 記事（Post）の CRUD API が1本動く。Swagger UI から叩ける。pytest で動作を確かめられる | 12 |
| **第2部** | ブログ API として完成する。リレーション・JWT ログイン・権限・画像・検索・ページング・メール・ソフトデリート | 14 |
| **第3部** | EC 風に拡張する。カート → 注文確定まで。トランザクションと同時実行で在庫が壊れない | 9 |
| **第4部** | React の画面（3〜4画面）から API を叩ける | 5 |
| **PJ** | roadmap.sh の URL Shortening Service を、本編とは別に自力で組む | 1本 |

**第1部だけで成果物になります。** 第1部を終えた時点で「MySQL に保存し、Swagger UI から操作でき、テストが通る API」が手元に残ります。
ここで止めても構いません。第2部に進むかどうかは、第1部を終えてから決めてください。

目安: 学習日は週4日（月・水・木・土）。1日1ステップで、第1部は約3週間です。

---

## 2. 環境準備

本編（第1部 ステップ1）の前に、一度だけ行います。
コマンドはすべて**リポジトリ直下**で実行します。

### 2.1 Python とライブラリ

> 🧒 **かみくだくと**: uv は「Python 本体とライブラリをまとめて管理する道具」。
> npm と nvm を1つにしたものに近い。ライブラリは `.venv/`（このリポジトリ専用の箱）に入る。

```bash
# pyproject.toml を作る（--bare: サンプルの main.py などを作らない）
uv init --bare --python 3.14

# このリポジトリで使う Python を 3.14 に固定する（.python-version ができる）
uv python pin 3.14

# 本体: Django 5.2 系 / Django Ninja / MySQL ドライバ（PyMySQL）
uv add "django>=5.2,<6.0" django-ninja pymysql

# 開発用: リンタ兼フォーマッタ / 型チェッカ / Django 用の型情報 / PyMySQL の型情報
uv add --dev ruff mypy "django-stubs[compatible-mypy]>=5.2,<6.0" types-PyMySQL

# Django プロジェクトを作る（設定置き場は config/。末尾の . で「ここに作る」）
uv run django-admin startproject config .

# アプリを2つ作る（ユーザー用と、ブログ用）
uv run python manage.py startapp accounts
uv run python manage.py startapp blog
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / django-ninja 1.7.1 / PyMySQL 1.2.3 / uv 0.12（2026-10-06）

**ここで `migrate` は実行しないでください。** ステップ1-2 でユーザーモデルを差し替えてから、ステップ1-3 で初めて実行します（理由は 1-2 で扱います）。

> 💡補足: MySQL ドライバは **PyMySQL** を使います。
> もう1つの候補 mysqlclient は C 言語の部品をビルドするため、macOS では `pkg-config` と MySQL クライアントの事前インストールが必要です。
> 実際にこの環境では `pkg-config` が無くビルドに失敗しました。PyMySQL は Python だけで書かれているので、この手間がありません。
> 根拠: https://docs.djangoproject.com/en/5.2/ref/databases/#mysql-db-api-drivers

> 💡補足: Django は 5.2 系を使います。5.2 は LTS（長期サポート版）で、2028年4月までセキュリティ修正が出ます。
> 最新は 6.x ですが、教材の前提（5.x）に合わせます。
> 根拠: https://www.djangoproject.com/download/#supported-versions

> 💡補足: Python は最新の安定版 **3.14** を使います（3.15 は 2026-10-06 時点でまだリリース候補版）。
> Django 5.2 は 5.2.8 から Python 3.14 に対応しています。
> 根拠: https://docs.djangoproject.com/en/5.2/faq/install/#what-python-version-can-i-use-with-django
> 手元の 3.14 を最新のパッチ版（3.14.7 など）に上げるには `uv python upgrade 3.14` を使います。

### 2.2 ruff と mypy の最小設定

`pyproject.toml` の末尾に追記します（差分）。

```toml
[tool.ruff]
line-length = 100
target-version = "py314"
extend-exclude = ["**/migrations/*"]   # 自動生成ファイルは対象外

[tool.ruff.lint]
select = ["E", "F", "I", "B", "DJ"]    # 基本 + import 順 + バグの芽 + Django 向け

[tool.mypy]
python_version = "3.14"
plugins = ["mypy_django_plugin.main"]  # Django のモデルを型として理解させる
exclude = ["/migrations/"]

[tool.django-stubs]
django_settings_module = "config.settings"
```

```bash
uv run ruff check --fix .   # 雛形に残る未使用 import（4件）を自動で消す
uv run ruff format .        # 書式を揃える
uv run mypy .               # 型チェック
```

✅ 検証済み: ruff 0.16.10 / mypy 1.19.1 / django-stubs 5.2.9

この時点の mypy は `ALLOWED_HOSTS` で1件エラーになります。**それで正常です。** ステップ1-1 で `settings.py` を直すと消えます。

> 🧒 **かみくだくと**: ruff は「書き方の間違いと見た目を直す道具」（ESLint + Prettier に相当）。
> mypy は「型の食い違いを実行前に見つける道具」（`tsc --noEmit` に相当）。

### 2.3 MySQL を Docker で起動する

`compose.yaml`（新規・全文）

```yaml
services:
  db:
    image: mysql:8.4
    environment:
      MYSQL_ROOT_PASSWORD: rootpass
      MYSQL_DATABASE: blog
      MYSQL_USER: django
      MYSQL_PASSWORD: django
    ports:
      - "127.0.0.1:3307:3306"   # ホストの 3307 → コンテナの 3306
    volumes:
      - db-data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 5s
      retries: 10

volumes:
  db-data:
```

```bash
docker compose up -d --wait   # 起動し、healthcheck が通るまで待つ
docker compose exec db mysql -udjango -pdjango blog -e "SELECT VERSION();"   # 8.4.x と出れば OK
```

✅ 検証済み: Docker 29.8 / MySQL 8.4.11

> 💡補足: ホスト側を **3307** にしているのは、別の学習リポジトリ（roadmap-sh-fastapi）の MySQL が 3306 を使っているためです。
> 両方を同時に起動できます。

> 🔓 **教材用の簡略化**: パスワードを `compose.yaml` に直接書いている。
> **本番では**: 環境変数やシークレット管理から渡す。第2部ステップ1で `.env` に移す。
> 根拠: https://hub.docker.com/_/mysql （"Docker Secrets" の節）

Django から MySQL への接続設定（`settings.py` の `DATABASES`）は、ステップ1-1 で書きます。

---

## 3. 完成時のディレクトリ構成

```
roadmap-sh-django/
├── README.md                      到達点と進捗
├── compose.yaml                   MySQL（環境準備で作る）
├── pyproject.toml / uv.lock       依存ライブラリと ruff / mypy の設定
├── manage.py                      Django のコマンド窓口
├── config/                        settings.py / urls.py / api.py（Ninja の入口）
├── accounts/                      カスタムユーザーモデル（第1部）/ Profile・ログイン（第2部）
├── blog/                          Post（第1部）/ Category・Tag・Comment・画像（第2部）
├── shop/                          Product・Cart・Order（第3部）
├── tests/                         pytest（第1部の最後から）
├── media/                         アップロード画像（第2部・git 管理外）
├── frontend/                      React（第4部）
├── docs/
│   ├── _prompt.md                 教材生成プロンプト
│   ├── _roadmap-django-source.md  素材（roadmap.sh のトピック）
│   ├── _glossary.md               用語集（毎ステップ追記）
│   ├── 00-plan.md                 このファイル
│   ├── p1-basics.md 〜 p4-react.md
│   ├── ext/
│   │   ├── _index.md              拡張モジュール一覧
│   │   └── celery.md 等
│   └── 99-uncovered.md            M3 の出力
└── projects/
    ├── _template/                 新規追加用の雛形
    └── url-shortening-service/    PJ（自己完結の別アプリ）
```

見てほしいのは、**本編のアプリがリポジトリ直下に並ぶ**ことです（`app/` の下には入れません）。
`projects/` の中だけは、本編と独立した別アプリになります。

---

## 4. ステップ一覧

**数え方のルール**: 「初出」は Django / Ninja の API・設定・記法のうち、その回で初めて**説明する**もの。1ステップ最大2つ。
`manage.py` のサブコマンド（`migrate`・`shell` など）は道具として扱い、初出には数えません。使う回で1〜2行説明します。

### 第1部 — Django の土台 → 手書き → Ninja → CRUD

| # | タイトル | 作るもの | 初出（Django/Ninja） | 重要度 |
| --- | --- | --- | --- | --- |
| 1-1 | プロジェクトを動かす | MySQL につながった状態で `runserver` が起動する | `settings.py`, `urls.py` | 🔴 |
| 1-2 | カスタムユーザーモデル | `accounts.User` を定義し、Django に「これを使え」と伝える | `AbstractUser`, `AUTH_USER_MODEL` | 🔴 |
| 1-3 | モデルを書く → マイグレーション | `Post` が MySQL のテーブルになる（`SHOW COLUMNS` で確認） | `models.Model` とフィールド, マイグレーション | 🔴 |
| 1-4 | 管理画面でデータを入れて見る | 管理画面から Post を3件登録できる | `admin.site.register`, 管理画面 | 🟡 |
| 1-5 | `JsonResponse` で一覧 GET を手書き | `GET /api/posts/` が JSON 配列を返す | `JsonResponse`, `QuerySet` | 🔴 |
| 1-6 | `JsonResponse` で POST を手書き | JSON の読み取り・必須/型チェック・エラー形式を全部自分で書く | `csrf_exempt`, `objects.create()` | 🔴 |
| 1-7 | 同じものを Ninja で書き直す | 1-5・1-6 が数行に縮む。手書き版と差分で比べる | `NinjaAPI` とデコレータ, `Schema` | 🔴 |
| 1-8 | Swagger UI と OpenAPI | `/api/docs` から API を試せる。出力の形も宣言する | OpenAPI の自動生成, `response=` | 🔴 |
| 1-9 | 1件取得 | `GET /api/posts/{id}`。無ければ 404 の JSON | パスパラメータ, `get_object_or_404` | 🔴 |
| 1-10 | 更新 | `PATCH /api/posts/{id}`。送った項目だけ変わる | `exclude_unset`, `save()` | 🔴 |
| 1-11 | 削除 | `DELETE /api/posts/{id}` が 204 を返す | `delete()`, ステータスコードの指定 | 🔴 |
| 1-12 | テストで固定する | CRUD の pytest が通る（テスト用 DB の権限もここで設定） | `pytest.mark.django_db`, Ninja `TestClient` | 🔴 |

山場は **1-6 → 1-7** です。手書きで苦労した部分が、Ninja でどこに消えたかを並べて見ます。
1-1〜1-12 では認証も pre-commit も入れません。全エンドポイント公開で進めます。

### 第2部 — ブログ API として完成させる

| # | タイトル | 作るもの | 初出（Django/Ninja） | 重要度 |
| --- | --- | --- | --- | --- |
| 2-1 | API をアプリごとに分ける | `blog/api.py` に分割。pre-commit 導入、秘密情報を `.env` へ | Ninja `Router`, 環境変数からの設定読み込み | 🔴 |
| 2-2 | カテゴリ（多対一） | Post が1つの Category に属する | `ForeignKey`, `on_delete` | 🔴 |
| 2-3 | タグ（多対多） | Post に複数の Tag。レスポンスに入れ子で出す | `ManyToManyField`, 入れ子の `Schema` | 🔴 |
| 2-4 | N+1 問題を見て直す | 一覧の SQL 本数を数え、1〜2本に減らす | `select_related`, `prefetch_related` | 🔴 |
| 2-5 | ミドルウェア | 全リクエストの所要時間をログに出す | `MIDDLEWARE`（自作）, `LOGGING` | 🟡 |
| 2-6 | JWT でログイン | ログイン API がトークンを返す。セッション認証との比較表 | `authenticate()`, `RefreshToken` | 🔴 |
| 2-7 | 認証と権限 | 作成は要ログイン。更新・削除は自分の記事だけ（403） | `JWTAuth`（`auth=`）, `HttpError` | 🔴 |
| 2-8 | ユーザー登録とプロフィール（一対一） | 登録 API と Profile | `create_user()`, `OneToOneField` | 🔴 |
| 2-9 | コメントと返信（自己参照） | Comment が Comment にぶら下がる | `ForeignKey("self")`, `related_name` | 🟡 |
| 2-10 | 画像アップロード | 1記事に複数枚の画像を保存する | `ImageField` と `MEDIA_ROOT`, `UploadedFile` | 🔴 |
| 2-11 | 検索と絞り込み | `?q=` でタイトル・本文を検索 | フィールドルックアップ（`__icontains`）, `Q` | 🔴 |
| 2-12 | ページング | 一覧が `limit` / `offset` で分割される | `@paginate`, `order_by()` | 🔴 |
| 2-13 | メール送信 | コメントが付いたら投稿者に通知（コンソール出力） | `send_mail()`, `EMAIL_BACKEND` | 🟡 |
| 2-14 | ソフトデリート | 削除しても行は残り、一覧からは消える | 抽象モデル, カスタムマネージャ | 🟡 |

### 第3部 — EC 風への拡張

| # | タイトル | 作るもの | 初出（Django/Ninja） | 重要度 |
| --- | --- | --- | --- | --- |
| 3-1 | 商品と在庫 | `shop` アプリ。Product・ProductImage・Inventory | `DecimalField`, `CheckConstraint` | 🔴 |
| 3-2 | カート | 同じ商品は1行にまとめて数量を足す | `UniqueConstraint`, `get_or_create()` | 🔴 |
| 3-3 | 注文を確定する | Cart → Order。購入時の価格を OrderItem に写す | `transaction.atomic`, `bulk_create()` | 🔴 |
| 3-4 | 同時に買うと壊れる | 最後の1個を2人が同時に買う状況を再現する | `F()` 式 | 🔴 |
| 3-5 | 行ロックで守る | 在庫の行を押さえてから減らす | `select_for_update()`, 分離レベル | 🟡 |
| 3-6 | 注文ステータス | 「確定 → 発送 → 完了」以外の遷移を拒否する | `TextChoices`, モデルメソッド | 🔴 |
| 3-7 | レビューと集計 | 商品一覧に平均評価と件数を付ける | `annotate()`, `Avg` / `Count` | 🔴 |
| 3-8 | トランザクションのテスト | ロールバックとコミット後処理をテストする | `django_db(transaction=True)`, `on_commit()` | 🟡 |
| 3-9 | クエリの総点検 | 注文履歴 API の SQL を最小にし、実行計画を見る | `Prefetch`, `explain()` | 🟡 |

### 第4部 — React から叩く

| # | タイトル | 作るもの | 初出（Django/Ninja） | 重要度 |
| --- | --- | --- | --- | --- |
| 4-1 | CORS | Vite の開発サーバから API を呼べる | django-cors-headers（`CORS_ALLOWED_ORIGINS`） | 🔴 |
| 4-2 | OpenAPI から型を作る | Ninja のスキーマから TypeScript の型を生成 | （なし。1-8 の OpenAPI を再利用） | 🟡 |
| 4-3 | 記事の一覧・詳細画面 | 一覧 → 詳細の2画面 | （なし） | 🟡 |
| 4-4 | ログイン画面 | JWT の保存と期限切れ時の更新 | （なし。2-6 の再利用） | 🔴 |
| 4-5 | カートと注文画面 | カートに入れて注文を確定する | （なし） | 🟡 |

### PJ — URL Shortening Service

第1部を終えたら挑戦できます。`MP: url-shortening-service` で呼びます。
アクセス回数のカウントで `F()` 式が要りますが、PJ 内で「本編に無い新しい軸」として扱います。

---

## 5. トピック対応表

素材（`docs/_roadmap-django-source.md`）の全113トピックの行き先です。
同名のトピック（migrations・templates・urls.py）は1行にまとめています。

### 本編で扱う

| トピック | 行き先 |
| --- | --- |
| introduction / installing--django / virtual-envs | 環境準備 |
| mysql / setting-up-the-database | 環境準備・1-1 |
| projects--apps / managepy / settingspy / running-your-project | 1-1 |
| urlspy（2件）/ url-patterns | 1-1・1-5 |
| custom-user-model / built-in-user-model | 1-2（標準ユーザーとの違いとして） |
| models / modelspy / fields-types / field-options / migrations（2件） | 1-3 |
| django-orm | 1-3・1-5 |
| django-admin / adminpy | 1-4 |
| views / viewspy / function-based-views | 1-5 |
| request-reponse-flow / the-mvc-model | 1-5（図で。テンプレートを使わない構成として） |
| querying-data / django-shell | 1-5 |
| create-update-delete | 1-6・1-10・1-11 |
| csrf | 1-6（`csrf_exempt` の理由）・2-6（JWT との比較表） |
| debugging | 1-6（トレースバックの読み方） |
| django-ninja / why-use-web-frameworks | 1-7（手書きとの差分が答え） |
| path-converters | 1-9 |
| pytest / django-test-framework / testspy / unittest--testcase | 1-12（`TestCase` は比較で触れる）・3-8 |
| model-relationships | 2-2・2-3・2-8・2-9 |
| query-optimization | 2-4・3-9 |
| middleware / routing-middleware / customization（custom middleware） | 2-5 |
| logging / loggers / handlers | 2-5（ミドルウェアのログ出力に必要な範囲） |
| authentication | 2-6 |
| authorization / users--permissions | 2-7 |
| media | 2-10 |
| filtering--lookups | 2-11 |
| pagination | 2-12 |
| model-inheritance | 2-14（抽象モデル） |
| transactions | 3-3・3-5・3-8 |
| model-methods | 3-6 |
| aggregations | 3-7 |

### 拡張モジュールへ回す

| トピック | 行き先 |
| --- | --- |
| background-tasks / celery | `MX: celery` |
| caching | `MX: cache` |
| signals | `MX: signals` |
| django--rest-framework / serializers / routers / views--viewsets | `MX: drf`（比較のみ） |
| asynchronous-django | `MX: websocket` で一部（ASGI）。本編は同期で統一する |

### 扱わない（理由つき）

| トピック | 理由 |
| --- | --- |
| templates（2件）/ dtl-syntax / variables / if / for / comments / filters--custom-filters / tags--custom-tags / template-inheritance | SSR 系。この教材は JSON を返す API だけを作る |
| django-forms / form-validation / model-forms | SSR 系。入力の検査は Ninja の `Schema` が担う（1-7） |
| class-based-views / generic-views / listview / detailview / createview / updateview / deleteview / customizing-views | SSR 系（クラスベースビュー）。ビューは関数 + Ninja で書く |
| message-framework | 画面に一度だけ出す通知の仕組み。画面を返さない API では使わない |
| static / static-files / whitenoise | API サーバは CSS/JS を配信しない。管理画面の分は開発サーバが自動で配る |
| error-pages | HTML のエラーページ。API のエラーは JSON で返す（1-6・1-9 で扱う） |
| named-urls / reverse-url | 主な用途はテンプレート内のリンク生成。API の URL は OpenAPI で共有する |
| regex-paths | `path()` とパスパラメータで足りる |
| admin-customization | 管理画面は「データを見る窓」として使うだけ |
| django-allauth | セッション前提の認証パッケージ。本教材は JWT 方針 |
| sqlite / postgresql / mariadb | DB は MySQL に統一する |
| raw-sql | ORM で足りる範囲に絞る。SQL は「ORM が出したもの」を読む側で扱う |
| custom-fields | 標準フィールドで全テーブルを表現できる |
| fixtures | テストデータは pytest のフィクスチャで作る |
| debug_toolbar / django_silk | HTML ページに情報を出す道具で、JSON API とは相性が悪い。SQL の本数は 2-4 でテストから数える |
| pdb-ipdb | VSCode のデバッガ（debugpy）を使う |
| filters（logging）/ formatters | ログの絞り込み・整形は運用の話。2-5 の最小構成で足りる |
| localization | 多言語対応。必要になれば拡張モジュールに足す |
| deployment / production-checklist | デプロイは範囲外。本番との差は 🔓 ラベルで毎回示す |
| how-the-web-works | 既知（HTTP・クライアント/サーバは TypeScript/React 経験で足りる） |

---

## 6. 拡張モジュール一覧

`docs/ext/_index.md` に同じ表があります。本編を終えたあとに選びます。

| name | 内容 | 前提 | 新しく必要なもの | 目安ステップ |
| --- | --- | --- | --- | --- |
| `celery` | 非同期処理（画像リサイズ・一括メール） | 第3部まで | Redis コンテナ | 3〜4 |
| `websocket` | リアルタイム通知 | 第3部まで | Django Channels / Redis | 3〜4 |
| `search` | 全文検索 | 第2部まで | Elasticsearch コンテナ | 3〜4 |
| `cache` | キャッシュ機構 | 第2部まで | Redis コンテナ | 2〜3 |
| `signals` | シグナル（と使いすぎの危うさ） | 第2部まで | なし | 1〜2 |
| `drf` | DRF なら同じ API をどう書くか（比較のみ） | 第2部まで | djangorestframework | 1〜2 |

---

## 7. 範囲外の予告（M3 で詳しく）

- **SSR 一式**（テンプレート・フォーム・クラスベースビュー・静的ファイル）
- **OAuth / ソーシャルログイン**（django-allauth など）
- **多言語対応**（localization）
- **決済**（注文確定まで。支払いは作らない）
- **デプロイと本番設定**（`manage.py check --deploy`、WSGI/ASGI サーバ、静的ファイル配信）
- **非同期ビュー**（`async def` のビュー。本編は同期で統一）
- **MySQL 以外の DB**、生 SQL、カスタムフィールド
- **プロファイリング道具**（debug toolbar / django-silk）

---

❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: 環境準備（§2）を済ませてから `M1: 第1部 ステップ1` — プロジェクトを動かす
