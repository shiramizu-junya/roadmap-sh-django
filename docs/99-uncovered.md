# 締め（M3）— つまずき・まとめ・範囲外

本編（第1部〜第4部）は、ここで終わりです。この章は、新しいことを覚える回ではありません。

1. つまずきやすかったところを、症状から引けるようにまとめる
2. 全体を1枚の地図にして、どこで何を学んだかを振り返る
3. この教材で**扱わなかったこと**を、理由と「次に読むもの」付きで並べる

分からないまま残った箇所は、`# TODO: わからん` の印だけ見返せば十分です。

---

## 1. つまずきやすかったところ

エラーの文や症状から引いてください。右の列の回に、詳しい説明と確かめた結果があります。

### 1-1. 環境と設定

| 症状 | 原因 | 直し方 | 回 |
| --- | --- | --- | --- |
| `OperationalError`（MySQL につながらない） | Docker（MySQL のコンテナ）が止まっている | `docker compose up -d` で起こしてから動かす | 1-1 |
| `KeyError: 'DB_NAME'` | `.env` が読まれていない、または項目が無い | `.env` の場所と名前を確かめる。`.env` はコミットしない | 2-1 |
| テストで `Access denied ... to database 'test_...'` | テストは `test_` で始まる別の DB を作る。その権限が無い | DB のユーザーに、`test_` の DB を作る権限を渡す | 1-12 |
| テストで `RuntimeError: Database access not allowed` | テストの引数に `db`（DB を使う許可）が無い | 引数に `db` か、`db` を使うフィクスチャ（`user` など）を書く | 1-12 |

### 1-2. モデルとマイグレーション

| 症状 | 原因 | 直し方 | 回 |
| --- | --- | --- | --- |
| `fields.E120` | `CharField` に `max_length` が無い | 長さの上限を書く | 1-3 |
| `IntegrityError (1062, "Duplicate entry ...")` | 一意（1つだけ）の決まりを破った | 先に `exists()` で調べて 409 を返す。最後の守りは DB の制約 | 2-8・3-2 |
| `ProtectedError` | `on_delete=PROTECT` の先を消そうとした | 参照している行を先に片付ける。消せないのが正しい場合もある | 2-2 |
| `RelatedObjectDoesNotExist`、または一覧が丸ごと 500 | 一対一の先（プロフィール・在庫）の行が無い。在庫の無い商品が1件あるだけで、一覧全体が落ちる | 親を作るときに、一緒に作る（`atomic` で1かたまりに） | 2-8・3-1 |

### 1-3. ORM と SQL

| 症状 | 原因 | 直し方 | 回 |
| --- | --- | --- | --- |
| 件数が増えると遅い。SQL が件数ぶん出る | N+1 問題。関連の先を1件ずつ取りに行っている | `select_related`（JOIN）か `prefetch_related`（まとめて1本）。テストで本数を固定する | 2-4・3-9 |
| 件数と平均を一緒に数えると、件数が増える | 2つの関連を JOIN すると、行が掛け算で増える | `Count("...", distinct=True)` | 3-7 |
| `FieldError: Cannot resolve keyword ...` | `__` でたどる名前が違う。または付け足した名前が項目とぶつかった | `related_name` と項目名を確かめる。付け足す名前は項目と変える | 3-9・第3部の宿題 |

### 1-4. トランザクションと同時実行

| 症状 | 原因 | 直し方 | 回 |
| --- | --- | --- | --- |
| 在庫1なのに2人が買えた | 「読んで、計算して、書く」の間に、別のリクエストが割り込んだ | `F()` で計算を DB にさせ、条件も `WHERE` に入れる | 3-4 |
| 同じ人の2度押しで、注文が2つできた | 同じカートを2つのリクエストが同時に読んだ | `atomic` の中で `select_for_update()`（行ロック） | 3-5 |
| `TransactionManagementError: select_for_update cannot be used outside of a transaction.` | `select_for_update()` を `atomic` の外で使った | `with transaction.atomic():` の中に入れる | 3-5 |
| 直す前のコードでもテストが通ってしまう | テストが2人を**順番に**通していて、同時にならない | `django_db(transaction=True)` とスレッドで、本当に同時に走らせる | 3-8 |
| 取り消された注文の確認メールが届く | `atomic` の中でメールを送った。取り消しはメールを戻せない | `transaction.on_commit()` で、確定したあとに送る | 3-8 |

### 1-5. 認証と権限

| 症状 | 原因 | 直し方 | 回 |
| --- | --- | --- | --- |
| 401 と 403 の使い分けで迷う | 401 は「誰か分からない」、403 は「分かったが、してよくない」 | 身分証の確認は `JWTAuth`、持ち主の確認はビューの中で `HttpError(403)` | 2-7 |
| `/auth/refresh` に access を渡すと 401 | 身分証（access）と引換券（refresh）は種類が違う | 更新には refresh を渡す | 2-6 |

### 1-6. 画面（React）から呼ぶとき

| 症状 | 原因 | 直し方 | 回 |
| --- | --- | --- | --- |
| Django は 200 なのに、画面は `Failed to fetch` | CORS。別のオリジンの画面には、許可のヘッダが無いと読ませない | django-cors-headers の `CORS_ALLOWED_ORIGINS` | 4-1 |
| `(corsheaders.E014) ... should not have path` | オリジンの最後に `/` を付けた | `http://localhost:5173` のように、方式・ホスト・ポートだけ | 4-1 |
| Console に同じエラーが2回 | 開発中だけ、`StrictMode` が effect を2回走らせる | 気にしなくてよい。本番のビルドでは1回 | 4-1 |
| `npm install` が `peer typescript@"^5.x"` で断られる | openapi-typescript 7.13.0 は TypeScript 5 の部品を使う。この画面は TypeScript 7 | `npx -p typescript@5.9.3 -p openapi-typescript@7.13.0` で、プロジェクトの外で動かす | 4-2 |
| 無い記事を開くと、画面が真っ白 | `fetch` は 404 でも失敗にしない。`{"detail": ...}` を記事として使った | `res.ok` を見て、2xx 以外は例外にする | 4-3 |
| `error TS1005: ';' expected` や `Unterminated regular expression literal` が大量に出る | JSX（`<p>…</p>`）を書いたファイルの拡張子が `.ts` | `.tsx` にする。JSX が書けるのは `.tsx` だけ | 4-5 |
| 5分たつとログインし直し | 身分証（access）の期限が切れた | 401 が来たら、引換券で取り替えて1回だけやり直す | 4-4 |
| `409 Conflict` とだけ出て、理由が分からない | 画面がステータスしか見ていない | Django の `detail` を読んで、例外の文に使う | 4-5 |
| 削除したのに `SyntaxError: ... Unexpected end of JSON input` | 204 は本文が空。`res.json()` が落ちる。Django では削除は成功している | 204 のときは本文を読まない | 第4部の宿題 |

---

## 2. まとめ — 全体の地図

### 2-1. 作ったもの

| 部 | 手元にできたもの | 中心になった考え方 |
| --- | --- | --- |
| 第1部 | 記事の CRUD API（`JsonResponse` の手書き → Ninja） | 宣言（`Schema`）から、検証と説明書（OpenAPI）が付いてくる |
| 第2部 | 登録・ログイン・権限・検索・ページング・画像・コメント・メール・ソフトデリートの付いたブログ API | 関連と SQL の本数を読み、「誰か」と「してよいか」を分けて守る |
| 第3部 | 商品・在庫・カート・注文・レビューの EC 風 API | 正しさを DB のそばで守る（制約・トランザクション・行ロック） |
| 第4部 | ログイン付きの React の画面（記事・商品・カート・注文） | API の呼び出しを1か所にまとめ、Django の答えをそのまま利用者に届ける |

テストは `59 passed`（第3部-8 の残りの3件を書けば `62 passed`）。画面は `npm run build` とブラウザで確かめました。

### 2-2. 1つのリクエストが通る道

「注文を確定する」ボタンを押したとき、どこを通るかです。上から順に読んでください。

```text
  React の画面（Cart.tsx）
    │  postJsonWithAuth('/orders')                 … 4-5
    ▼
  src/api/client.ts（sendWithAuth）
    │  Authorization: Bearer <access> を付ける     … 4-4
    │  401 なら引換券で取り替えて、もう1回          … 4-4
    ▼
  ブラウザ
    │  別のオリジンなので、先に OPTIONS で下見      … 4-1・4-4
    ▼
  Django のミドルウェア（CorsMiddleware など）     … 2-5・4-1
    ▼
  Ninja（URL → 関数。JWTAuth で身分証を確かめる）   … 1-7・2-6
    ▼
  place_order
    │  atomic の中で、カートの行に鍵（select_for_update）… 3-3・3-5
    │  注文・明細を作り、在庫を F() で減らす        … 3-3・3-4
    │  足りなければ HttpError(409) → 全部取り消し    … 3-3
    │  確定したらメール（on_commit）                … 3-8
    ▼
  MySQL（制約で最後の守り）                         … 3-1・3-2
    ▼
  201 か {"detail": "理由"} が、同じ道を戻って画面に出る … 4-5
```

✅ 検証済み: 図の各段は、右に書いた回で動かして確かめたもの

### 2-3. 本番に持っていくときに変えるもの（🔓 の総まとめ）

本編では、分かりやすさのために本番と違う書き方をした箇所に 🔓 を付けました。本番に出すときは、ここを順に見直します。

| 回 | 教材での書き方 | 本番では |
| --- | --- | --- |
| 1-1 | `DEBUG = True`、`ALLOWED_HOSTS`、DB のパスワードを直接書く | 環境変数から読み、`DEBUG = False`。`manage.py check --deploy` を通す |
| 1-6 | `csrf_exempt` で検査を外す | Cookie で認証するなら CSRF の検査を戻す。JWT をヘッダで送るなら不要（2-6 の比較表） |
| 1-8 | `/api/docs` を誰でも見られる | `NinjaAPI(docs_decorator=staff_member_required)` などで、見られる人を絞る |
| 1-9・4-3・4-5 | 404 の内部の文（`No Post matches ...`）が画面まで出る | 利用者向けの言葉に変える |
| 2-6・4-4 | 期限は既定のまま。引換券は何度でも使える。身分証と引換券を `localStorage` に入れる | 使った引換券を無効にする（`ROTATE_REFRESH_TOKENS` など）。署名の鍵は `SIGNING_KEY` で分ける。引換券は `HttpOnly` の Cookie、身分証はメモリだけ。ログアウトで引換券を無効にする（第4部の宿題 Lv3） |
| 2-8 | パスワードの条件は「8文字以上」だけ | `validate_password()` で、よくあるパスワードも弾く |
| 2-10 | 画像を Django 自身が `media/` から配る | ストレージを S3 などに差し替え、配るのは Web サーバや CDN に任せる |
| 2-13 | メールは画面に出すだけ | 本物の送信サービスにつなぐ。時間がかかるなら、レスポンスのあとに回す（`MX: celery`） |
| 4-1・4-2 | 許すオリジンと `API_URL` を直接書き、型の材料も動いている Django から取る | 環境変数から読む。型は `export_openapi_schema` で書き出したファイルから作る |
| 4-3 | どの URL にも `index.html` を返すのは Vite の開発サーバ | 画面を配るサーバにも、同じ設定を入れる |

根拠: https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

---

## 3. この教材で扱わなかったこと

`docs/00-plan.md` の §5「扱わない」と §7「範囲外の予告」から並べています。素材（roadmap.sh の Django ロードマップ）のトピックのうち、本編にも拡張モジュールにも入れなかったものです。

### 3-1. 画面を Django で作る仕組み（SSR 一式）

| トピック | 中身 | 扱わなかった理由 | 次に読むもの |
| --- | --- | --- | --- |
| テンプレート（DTL・継承・フィルタ・タグ） | HTML を Django が組み立てて返す | この教材は JSON を返す API だけを作った。画面は React が作る | https://docs.djangoproject.com/en/5.2/topics/templates/ |
| フォーム（`forms`・`ModelForm`・検証） | HTML のフォームと、その入力の検査 | 入力の検査は Ninja の `Schema` が担った（1-7） | https://docs.djangoproject.com/en/5.2/topics/forms/ |
| クラスベースビュー（`ListView` など） | よくある画面をクラスで書く | ビューは関数と Ninja で書いた | https://docs.djangoproject.com/en/5.2/topics/class-based-views/ |
| メッセージ | 画面に一度だけ出す通知 | 画面を返さない API では使わない | https://docs.djangoproject.com/en/5.2/ref/contrib/messages/ |
| 静的ファイル・WhiteNoise | CSS や JS を配る | API サーバは CSS や JS を配らない。管理画面の分は開発サーバが配った | https://docs.djangoproject.com/en/5.2/howto/static-files/ ・ https://whitenoise.readthedocs.io/en/stable/ |
| エラーページ | 404 や 500 の HTML | API のエラーは JSON で返した（1-6・1-9） | https://docs.djangoproject.com/en/5.2/topics/http/views/#customizing-error-views |
| 名前付き URL・`reverse` | URL を名前から組み立てる | 主な使い道はテンプレートの中のリンク。API の URL は OpenAPI で画面と共有した（4-2） | https://docs.djangoproject.com/en/5.2/topics/http/urls/#reverse-resolution-of-urls |
| 正規表現の URL（`re_path`） | URL を正規表現で決める | `path()` とパスパラメータで足りた（1-9） | https://docs.djangoproject.com/en/5.2/ref/urls/#re-path |

### 3-2. 認証・多言語・決済

| トピック | 中身 | 扱わなかった理由 | 次に読むもの |
| --- | --- | --- | --- |
| OAuth・ソーシャルログイン（django-allauth） | Google などのアカウントでログインする | 認証は JWT（django-ninja-jwt）に絞った。外部サービスとの登録や画面の行き来が増え、1ステップに収まらない。React のような画面向けには、allauth に `allauth.headless` がある | https://docs.allauth.org/en/latest/headless/index.html |
| 多言語対応（i18n / l10n） | 文や日付の書き方を、利用者の言語に合わせる | 日本語だけで作った。必要になれば拡張モジュールに足す | https://docs.djangoproject.com/en/5.2/topics/i18n/ |
| 決済 | お金を受け取る | 注文の確定までで止めた。決済は外部サービス（Stripe など）とのやり取りで、Django の仕組みの外の話が大きい。二重請求を防ぐ「同じ要求は1回分にする」考え方（冪等キー）は、3-5 の二重注文と同じ問題 | https://docs.stripe.com/payments/payment-intents ・ https://docs.stripe.com/api/idempotent_requests |

### 3-3. 本番と運用

| トピック | 中身 | 扱わなかった理由 | 次に読むもの |
| --- | --- | --- | --- |
| デプロイ・本番の点検 | 本物のサーバで動かす。WSGI / ASGI のサーバ、`check --deploy` | 範囲外。本番との違いは、毎回 🔓 で示した（2-3 の表） | https://docs.djangoproject.com/en/5.2/howto/deployment/ ・ https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/ |
| 非同期のビュー（`async def`） | 待ち時間の長い処理を、同時にたくさんさばく | 本編は同期で統一した。ORM の多くは、まだ同期が前提 | https://docs.djangoproject.com/en/5.2/topics/async/ ・ https://django-ninja.dev/guide/async/ |
| ログの絞り込み・整形（filters / formatters） | ログを出し分け、形をそろえる | 運用の話。2-5 の最小構成で足りた | https://docs.djangoproject.com/en/5.2/topics/logging/ |
| 管理画面のカスタマイズ | 管理画面の一覧や入力欄を作り込む | 管理画面は「データを見る窓」として使うだけにした | https://docs.djangoproject.com/en/5.2/ref/contrib/admin/ |

### 3-4. DB と道具

| トピック | 中身 | 扱わなかった理由 | 次に読むもの |
| --- | --- | --- | --- |
| SQLite・PostgreSQL・MariaDB | MySQL 以外の DB | DB は MySQL に統一した。分離レベルや制約の細かい動きは DB ごとに違う | https://docs.djangoproject.com/en/5.2/ref/databases/ |
| 生 SQL | ORM を通さずに SQL を書く | ORM で足りる範囲に絞った。SQL は「ORM が出したもの」を読む側で扱った（2-4・3-9） | https://docs.djangoproject.com/en/5.2/topics/db/sql/ |
| カスタムフィールド | 自分で項目の型を作る | 標準の項目で全部の台帳を表せた | https://docs.djangoproject.com/en/5.2/howto/custom-model-fields/ |
| fixtures（`loaddata`） | JSON などのファイルからデータを入れる | テストのデータは pytest のフィクスチャ、開発のデータは `scripts/seed.py` で作った | https://docs.djangoproject.com/en/5.2/topics/db/fixtures/ |
| django-debug-toolbar・django-silk | SQL や時間を画面で見る道具 | HTML のページに情報を出す道具で、JSON の API とは相性が悪い。SQL の本数はテストで数えた（2-4） | https://django-debug-toolbar.readthedocs.io/en/latest/ ・ https://github.com/jazzband/django-silk |
| pdb / ipdb | ターミナルで止めて調べる | エディタのデバッガ（debugpy）を使った | https://docs.python.org/3/library/pdb.html |
| Web の仕組み（how the web works） | HTTP やブラウザとサーバの関係 | TypeScript と React の経験で、もう知っている前提にした | https://developer.mozilla.org/en-US/docs/Learn_web_development/Getting_started/Web_standards/How_the_web_works |

### 3-5. 拡張モジュールに回したもの

本編では扱わず、`docs/ext/_index.md` の拡張モジュールに回しました。必要になったものだけ、`MX: <name>` で呼べます。

| トピック | 拡張モジュール | 前提 |
| --- | --- | --- |
| バックグラウンド処理・Celery（2-13 のメールを、レスポンスのあとに回す） | `MX: celery` | 第3部まで |
| キャッシュ | `MX: cache` | 第2部まで |
| シグナル | `MX: signals` | 第2部まで |
| Django REST Framework（Serializer・Router・ViewSet） | `MX: drf`（Ninja との比較だけ） | 第2部まで |
| 非同期の一部（ASGI） | `MX: websocket` | 第3部まで |
| 全文検索 | `MX: search` | 第2部まで |

---

## 4. ここから先

- **roadmap.sh のプロジェクト**: `MP: url-shortening-service` がまだ残っています。第1部の知識で作れて、アクセス回数を数えるところで 3-4 の `F()` が効きます
- **拡張モジュール**: 上の表から、必要になったものだけ
- **宿題**: `homework-p2`・`homework-p3`・`homework-p4` のブランチで、各部の宿題をまだやっていなければ
- **roadmap.sh の進捗**: `docs/00-plan.md` §8 の決まりどおり、全教材（拡張モジュールを含む）を終えたあとに1回だけまとめて付けます

**ここで止めても、成果物はそろっています。** ブログと EC 風の API、それをログイン付きで使う React の画面があり、API はテストで、画面はビルドとブラウザで動きを確かめられています。

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `MP: url-shortening-service` ／ または `MX: <name>`（`docs/ext/_index.md` から選ぶ）
