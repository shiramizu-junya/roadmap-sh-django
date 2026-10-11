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
| タプル | tuple | 複数の値をひと組にしたもの。`return 201, post` は2つの値の組を返す | 第1部-8 |
| パスパラメータ | path parameter（`{post_id}`） | URL の一部を値として受け取る仕組み。`/posts/3` の `3` を引数にする | 第1部-9 |
| 404 | 404 Not Found | 「探したものが無い」を表すステータス。`get_object_or_404` が無いときに返す | 第1部-9 |
| PATCH | HTTP PATCH | 一部だけ変える HTTP メソッド。送った項目だけを更新する | 第1部-10 |
| PUT | HTTP PUT | 全部を送り直して置き換える HTTP メソッド。この教材では使わない | 第1部-10 |
| 204 | 204 No Content | 「成功した。返す中身は無い」を表すステータス。削除の成功で使う | 第1部-11 |
| CRUD | Create / Read / Update / Delete | 作成・取得・更新・削除の4つの基本操作 | 第1部-11 |
