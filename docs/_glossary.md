# 用語集

分からない言葉が出てきたら、まずここを引く。
載っていなければ `?: <言葉>` と送ると、解説が返ってきてここに追記される。

| 用語 | 正式名称 | 🧒 かみくだくと | 初出 |
|---|---|---|---|
| プロジェクト | project | サイト全体の設定を持つ入れ物。この教材では `config/` | 環境準備 |
| アプリ | application | 機能ごとに分けた部品。`accounts/`・`blog/` など。プロジェクトに登録して使う | 環境準備 |
| 秘密鍵 | `SECRET_KEY` | ログイン状態などに「改ざんされていない印」を付ける鍵。漏れたら作り直す | 環境準備 |
| 環境変数 | environment variable | プログラムの外から渡す設定値。この教材では `.env` に書く | 環境準備 |
| 設定モジュール | settings module（`settings.py`） | Django 全体の振る舞いを決めるファイル。起動時に1回読まれる | 第1部-1 |
| URLconf | URLconf（`urls.py`） | 受付の案内表。リクエストのたびに `urlpatterns` を上から照合する | 第1部-1 |
| 開発サーバ | development server（`runserver`） | 開発用の簡易サーバ。ファイルを保存すると自動で再起動する | 第1部-1 |
| モデル | model | 台帳（テーブル）の設計図を Python のクラスで書いたもの | 第1部-2 |
| カスタムユーザーモデル | custom user model | 標準のユーザーの代わりに使う、自分のユーザーの設計図。最初の `migrate` の前に作る | 第1部-2 |
| 抽象モデル | abstract model（例: `AbstractUser`） | 項目を受け継がせるためだけのモデル。自分のテーブルは持たない | 第1部-2 |
| フィールド | field（`CharField` など） | 台帳の1列。種類ごとにクラスがある | 第1部-3 |
| マイグレーション | migration | 台帳を書き換える手続き。SQL は Django が作る。`makemigrations` で手続き書を作り、`migrate` で DB に流す | 第1部-3 |
| マイグレーションファイル | migration file | `migrations/0001_initial.py` など。手続き書。Git にコミットする | 第1部-3 |
| 管理画面 | Django admin | データを見るための窓。`admin.py` に1行書くと、そのモデルの一覧・追加画面ができる。学習対象ではない | 第1部-4 |
| スーパーユーザー | superuser | 管理画面に入れる、すべての権限を持つユーザー。`createsuperuser` で作る | 第1部-4 |
| ハッシュ | hash | 元に戻せない形に変えた値。パスワードはこの形で保存される | 第1部-4 |
| ビュー関数 | view function | 担当職員。リクエストを受け取り、レスポンス（返事）を作って返す関数 | 第1部-5 |
| ORM | Object-Relational Mapper | 台帳を代わりに引いてくれる職員。Python で書いた問い合わせを SQL にして DB に聞く | 第1部-5 |
| QuerySet | QuerySet | 「この条件で台帳を引く」という予定表。使うまで SQL を出さない | 第1部-5 |
| 遅延評価 | lazy evaluation | 必要になるまで実行しないこと。`QuerySet` は `for` などで中身が要るときに SQL を出す | 第1部-5 |
| CSRF | Cross-Site Request Forgery | 別のサイトから勝手に送信させる攻撃。Django は既定で POST などを検査し、印が無いと 403 で止める | 第1部-6 |
| デコレータ | decorator（`@`） | 直下の関数を包んで機能を足す書き方。`@csrf_exempt` など | 第1部-6 |
| バリデーション | validation | 申請書の書式チェック。受け取った値が必須・型・長さの条件を満たすか確かめること | 第1部-6 |
| Django Ninja | Django Ninja | Django の上に乗る薄い層。型注釈から入力の検査や API の説明書を作る | 第1部-7 |
| Pydantic | Pydantic | 型注釈をもとに値を検査・変換するライブラリ。Ninja の中で動く | 第1部-7 |
| スキーマ | schema（`ninja.Schema`） | 申請書の書式。何を・どの型で・どんな条件で受け取るかの宣言 | 第1部-7 |
| OpenAPI | OpenAPI Specification | API の説明書の決まった書き方（中身は JSON）。Ninja が宣言から自動で作る | 第1部-8 |
| Swagger UI | Swagger UI | OpenAPI の説明書を画面にし、ブラウザから API を試せる道具。`/api/docs` | 第1部-8 |
| Status | `ninja.Status` | ステータスと中身を一緒に返すための入れ物。`Status(201, post)` のように使う | 第1部-8 |
| パスパラメータ | path parameter（`{post_id}`） | URL の一部を値として受け取る仕組み。`/posts/3` の `3` を引数にする | 第1部-9 |
| 404 | 404 Not Found | 「探したものが無い」を表すステータス。`get_object_or_404` が無いときに返す | 第1部-9 |
| PATCH | HTTP PATCH | 一部だけ変える HTTP メソッド。送った項目だけを更新する | 第1部-10 |
| PUT | HTTP PUT | 全部を送り直して置き換える HTTP メソッド。この教材では使わない | 第1部-10 |
| 204 | 204 No Content | 「成功した。返す中身は無い」を表すステータス。削除の成功で使う | 第1部-11 |
| CRUD | Create / Read / Update / Delete | 作成・取得・更新・削除の4つの基本操作 | 第1部-11 |
| pytest | pytest | Python のテストを動かす道具。`test_` で始まる関数を探して実行する | 第1部-12 |
| テスト用 DB | test database（`test_blog`） | テスト専用の別の台帳。テストごとに変更を取り消し、終わると消える | 第1部-12 |
| assert | `assert` 文 | 条件が偽ならテストを失敗させる文 | 第1部-12 |
| Router | `ninja.Router` | 窓口の「部署」。アプリごとの API 一式をまとめ、`add_router` で本庁（`NinjaAPI`）に差し込む | 第2部-1 |
| pre-commit | pre-commit | コミットの直前に、ruff や mypy などの検査を自動で走らせる道具 | 第2部-1 |
| .env.example | — | `.env` の見本。秘密の値は入れず、Git に入れて共有する | 第2部-1 |
| 多対一 | many-to-one | 「記事は1つのカテゴリに属し、カテゴリには多くの記事」の関係。`ForeignKey` で表す | 第2部-2 |
| 外部キー | foreign key | 別の台帳の `id` を書いておく列（例: `category_id`）。無い `id` は DB が拒否する | 第2部-2 |
| on_delete | `on_delete` | 参照先が消されるときの決まり（`PROTECT` / `CASCADE` / `SET_NULL` など）。Django が実行する | 第2部-2 |
| 多対多 | many-to-many | 「記事に複数のタグ、タグに複数の記事」の関係。`ManyToManyField` で表す | 第2部-3 |
| つなぎの台帳 | 中間テーブル（through table） | 多対多の組（`post_id` と `tag_id`）を並べる台帳。`blog_post_tags` など。Django が自動で作る | 第2部-3 |
| N+1 問題 | N+1 query problem | 一覧の SQL 1本のあと、1件ごとに関連データを取りに行き、SQL が「1 + 件数」本になること | 第2部-4 |
| JOIN | JOIN | 2つの台帳を、つなぐ列（`category_id` など）で横に並べて1つの結果にする SQL | 第2部-4 |
| ミドルウェア | middleware | 窓口の順路に置かれた共通の検査。全リクエストが行きと帰りに通る。`MIDDLEWARE` の並び順に通る | 第2部-5 |
| ロガー | logger | ログを書き込む名前付きの出し口（`logging.getLogger(__name__)`）。どこまで画面に出すかは `LOGGING` で決める | 第2部-5 |
| ログレベル | log level | ログの重要度（`DEBUG` < `INFO` < `WARNING` < `ERROR`）。既定では `WARNING` 以上しか表示されない | 第2部-5 |
| JWT | JSON Web Token | 窓口が発行する身分証。`user_id` と期限が書かれ、サーバの署名が付く。中身はだれでも読めるが、書き換えると署名が合わなくなる | 第2部-6 |
| アクセストークン | access token | 身分証そのもの。API を呼ぶたびに見せる。期限が短い（既定5分） | 第2部-6 |
| リフレッシュトークン | refresh token | 新しいアクセストークンとの引換券。期限が長い（既定1日） | 第2部-6 |
| セッション認証 | session authentication | ログイン中の人をサーバが `django_session` に覚え、Cookie の `sessionid` で照らし合わせる方式。管理画面が使う | 第2部-6 |
| 認証 | authentication | 「あなたは誰か」を身分証（JWT など）で確かめること。失敗は 401 | 第2部-7 |
| 認可 | authorization | 「その人がこの手続きをしてよいか」を決めること。権限とも言う。失敗は 403 | 第2部-7 |
| 401 と 403 | 401 Unauthorized / 403 Forbidden | 401 は「誰か分からない」、403 は「誰かは分かったが許可がない」 | 第2部-7 |
| フィクスチャ | pytest fixture | テストの準備をする関数。`@pytest.fixture` を付け、テストの引数に同じ名前を書くと渡される | 第2部-7 |
| 一対一 | one-to-one（`OneToOneField`） | 1人に1つだけのつながり。つなぐ列に `UNIQUE` が付いた外部キーになる。逆向きは `user.profile` で引ける | 第2部-8 |
| ハッシュ | password hash | パスワードを決まった手順で崩した文字列。元には戻せない。照合は入力を同じ手順で崩して比べる | 第2部-8 |
| `create_user()` | `UserManager.create_user()` | ユーザーを作る専用の命令。パスワードをハッシュにしてから保存する。`objects.create()` だと平文のまま入り、ログインできない | 第2部-8 |
| 自己参照 | recursive relationship（`ForeignKey("self")`） | 台帳の行が、同じ台帳の別の行を指すこと。返信は「どのコメントへの返信か」を `parent_id` で覚える | 第2部-9 |
| `related_name` | related_name | 相手のモデルから逆向きにたどる入口の名前。`related_name="comments"` なら `post.comments` で引ける。付けないと `comment_set` | 第2部-9 |
| `assert` | assert 文 | 「ここでは必ずこの条件が真」という宣言。偽なら `AssertionError` で止まる。mypy は宣言のあとの型を絞り込む | 第2部-9 |
| メディアファイル | media files | 利用者が送ってきたファイル（画像など）。中身はディスクに置き、台帳には置き場所の文字列だけを書く | 第2部-10 |
| `MEDIA_ROOT`・`MEDIA_URL` | MEDIA_ROOT / MEDIA_URL | `MEDIA_ROOT` はメディアファイルを置くフォルダ、`MEDIA_URL` はそれを配る URL の頭（`/media/`） | 第2部-10 |
| `ImageField` | models.ImageField | 画像の置き場所を覚える列。DB では `varchar(100)` の文字列。Pillow が要る。モデルで保存するときは中身を確かめない | 第2部-10 |
| `UploadedFile` | UploadedFile | 送られてきたファイル。`name`・`size`・`read()` などを持つ。Ninja では引数の型に書くと受け取れる | 第2部-10 |
| multipart/form-data | multipart/form-data | 文字とファイルを区切り線で仕切って、1回で送る形式。`curl -F` やブラウザの `FormData` が使う | 第2部-10 |
| フィールドルックアップ | field lookups | `項目名__比べ方` の形で、どう比べるかを書く方法。`title__icontains="x"` は「title に x を含む（大文字・小文字は区別しない）」 | 第2部-11 |
| `Q` | Q オブジェクト（`django.db.models.Q`） | 条件を1つの部品にしたもの。`Q(a) \| Q(b)` で OR を表す。`filter()` を重ねた分は AND | 第2部-11 |
| クエリパラメータ | query parameters | URL の `?` の後ろ（`?q=x&category_id=2`）。Ninja では、パスに無い関数の引数がクエリパラメータになる | 第2部-11 |
| 照合順序 | collation | DB が文字を比べるときの決まり。`utf8mb4_0900_ai_ci` は大文字・小文字もアクセント（日本語の濁点も）も区別しない | 第2部-11 |
| ページング | pagination | 長い一覧を区切って返すこと。`limit` は何件返すか、`offset` は先頭から何件飛ばすか | 第2部-12 |
| `@paginate` | ninja.pagination.paginate | 一覧の関数に付けるデコレータ。`?limit=`・`?offset=` を受け取り、`{"items": [...], "count": 全件数}` で返す。`@router.get` の下に置く | 第2部-12 |
| `order_by()` | QuerySet.order_by() | 並び順を決める。`-` を付けると逆順（新しい順など）。最後に `id` を足すと順番が1つに決まる | 第2部-12 |
| メールバックエンド | email backend（`EMAIL_BACKEND`） | メールをどこへ届けるかを決める差し替え部品。開発は console（画面）、テストは locmem（メモリ）、本番は smtp | 第2部-13 |
| `send_mail()` | django.core.mail.send_mail | 件名・本文・差出人・宛先を渡してメールを送る。届け方は `EMAIL_BACKEND` に任せる | 第2部-13 |
| SMTP | Simple Mail Transfer Protocol | メールをサーバからサーバへ送る決まり。Django の既定のバックエンドは `localhost:25` の SMTP サーバに渡す | 第2部-13 |
| ヘッダインジェクション | header injection | 件名などに改行を混ぜて、メールの見出しを勝手に書き足す攻撃。Django は改行を見つけると `BadHeaderError` で止める | 第2部-13 |
| ソフトデリート | soft delete | 行を消さずに「消した印」（`deleted_at` など）を書き込むこと。台帳に残るので戻せる | 第2部-14 |
| マネージャ | Manager（`Post.objects`） | 台帳を引くときの窓口。最初に書いたものが既定の窓口になり、`get_object_or_404` や管理画面が使う | 第2部-14 |
| `abstract = True` | abstract base classes | `class Meta` に書くと、そのモデルの台帳は作られず、項目と窓口が継承した子に配られる。1-2 の `AbstractUser` も同じ仕組み | 第2部-14 |
| `get_queryset()` | Manager.get_queryset() | 窓口が最初に作る QuerySet。上書きして `filter()` を足すと、その窓口を使う SQL すべてに条件が付く | 第2部-14 |
| `DecimalField` | DecimalField（`max_digits`・`decimal_places`） | お金のための数の項目。小数を10進数のまま持つので、端数がずれない。MySQL では `numeric(10, 2)` になる | 第3部-1 |
| `Decimal` | decimal.Decimal（Python 標準） | 10進数の小数。必ず文字列から作る（`Decimal("2980")`）。API の JSON では `"2980.00"` という文字列で返る | 第3部-1 |
| チェック制約 | CheckConstraint（`Meta.constraints`） | 台帳そのものに貼る決まり（例: 在庫は0以上）。破る書き込みは、どこから来ても MySQL が断る | 第3部-1 |
| `IntegrityError` | django.db.IntegrityError | DB の決まり（制約・外部キー・UNIQUE）を破ったときに Django が投げる例外。API の中で起きると 500 | 第3部-1 |
| 一意制約 | UniqueConstraint（`Meta.constraints`） | 「この組み合わせの行は1つだけ」という台帳の決まり。破る書き込みは MySQL が 1062 Duplicate entry で断る | 第3部-2 |
| `get_or_create()` | QuerySet.get_or_create() | 探して、無ければ作る。戻り値は `(行, 作ったか)`。一意制約がある項目で使うと、同時に呼ばれても行は1つ | 第3部-2 |
| `defaults` | get_or_create(defaults=...) | `get_or_create()` で、新しく作るときだけ使う値。見つかったときは使われない | 第3部-2 |
| トランザクション | transaction | いくつもの書き込みを「全部やるか、何もしないか」の1かたまりにすること。MySQL では `BEGIN` 〜 `COMMIT` / `ROLLBACK` | 第3部-3 |
| `transaction.atomic` | django.db.transaction.atomic | `with` で囲んだ範囲を1つのトランザクションにする。ふつうに抜ければ確定、例外で抜ければ取り消し | 第3部-3 |
| コミット / ロールバック | commit / rollback | コミットは書き込みの確定。ロールバックは取り消しで、`BEGIN` の前の台帳に戻る（ただし `AUTO_INCREMENT` の番号は戻らない） | 第3部-3 |
| `bulk_create()` | QuerySet.bulk_create() | 何行もの INSERT を SQL 1本にまとめる。行ごとの `save()` は通らず、MySQL では作った行に `id` が入らない | 第3部-3 |
