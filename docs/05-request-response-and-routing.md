# リクエスト/レスポンスとルーティング 完全入門

> **このドキュメントの読み方**
> 上から順に読み、コードブロックを **自分の手で** プロジェクトに書き写しながら進めてください。各章末の「ハンズオン」が、その章の知識を使って既存の `polls/` アプリにルーティングやミドルウェアを足していきます。完走すると polls が「リクエスト ID を発行・X-Robots-Tag を付ける・カスタムパスコンバータで日付付き URL を扱える」アプリに育ちます。
>
> **前提**: `docs/01〜04` を概ね理解している状態。`config/urls.py` から `polls/urls.py` へ `include()` で繋がっていることを把握している。

---

## このドキュメントで作るもの

完走後の polls の状態：

| 項目 | できるようになること |
|---|---|
| Request 観察ビュー | `/polls/whoami/` で自分のリクエストオブジェクトの中身を一覧表示 |
| 日付パスコンバータ | `/polls/by-date/2026-05-15/` のような URL を `date` 型で受け取る |
| カテゴリパスコンバータ | `/polls/category/<chef\|foodie\|gourmand>/` のように許可値だけマッチさせる |
| reverse の徹底活用 | テンプレートとビュー両方で `name=` 経由の URL 生成 |
| カスタムミドルウェア | 各レスポンスに `X-Request-Id` ヘッダーを付与、リクエスト処理時間をログに出す |

完走後に身につく知識：
- ブラウザがリクエストを送ってから HTML が返ってくるまでの **全工程**（WSGI → middleware → URLconf → view → response）
- `HttpRequest` から **何が読めて何が読めないか**（GET / POST / FILES / META / headers / user / session）
- `HttpResponse` のサブクラスとステータスコード（リダイレクト / 404 / JSON / ファイル / ストリーミング）
- `path()` と `re_path()` の使い分け
- **5つのビルトインパスコンバータ** (`str` / `int` / `slug` / `uuid` / `path`) の詳細
- **カスタムパスコンバータ** の作り方（`regex` / `to_python` / `to_url`）
- 名前付き URL と `reverse()` / `{% url %}` / `get_absolute_url()` の使い分け
- **URL 名前空間**（`app_name` と `namespace=`）でアプリを複数インスタンス化する方法
- **ミドルウェア** の書き方・順序の意味・`process_view` / `process_exception` などのフック
- 標準ミドルウェア（`SecurityMiddleware`、`CsrfViewMiddleware`、`AuthenticationMiddleware` 等）が **何のために存在するか**

---

# 第1章 リクエスト/レスポンスの全体像

## 1-1. 「クリックして HTML が返ってくる」その間に何が起きているか

ブラウザで `http://127.0.0.1:8000/polls/1/` にアクセスしたとき、Django の内部では概ねこの順番で処理が走ります：

```
[1] ブラウザ
       │  HTTP リクエスト: GET /polls/1/ HTTP/1.1
       ▼
[2] WSGI / ASGI サーバ (runserver / gunicorn / uvicorn)
       │  environ という dict を組み立てる
       ▼
[3] Django の WSGIHandler / ASGIHandler
       │  environ を HttpRequest に詰める
       ▼
[4] MIDDLEWARE の前半 (上から順)
       │  SecurityMiddleware → SessionMiddleware → ... と通っていく
       │  各 middleware は request を加工 (例: request.session 付与)
       ▼
[5] URLconf (config.urls → polls.urls)
       │  パス "/polls/1/" にマッチする path() を探す
       │  見つかったら view 関数と引数を決定
       ▼
[6] MIDDLEWARE.process_view (もしあれば)
       │  view 直前のフック
       ▼
[7] View 関数 (例: polls.views.detail)
       │  models を叩く → DB に SQL 発行
       │  template をレンダリング
       │  HttpResponse を return
       ▼
[8] MIDDLEWARE の後半 (下から逆順)
       │  各 middleware は response を加工 (例: CSRF cookie 設定)
       ▼
[9] WSGI / ASGI サーバ
       │  HttpResponse を HTTP レスポンスに整形
       ▼
[10] ブラウザ
       HTTP レスポンス: HTTP/1.1 200 OK + 本文 (HTML)
```

これだけ多くのステップを経て1リクエストが処理されています。「`def view(request): return HttpResponse(...)`」の `request` がどこから来て、`return` した値がどこへ行くのか、という全体像を最初に頭に入れておくと、以降の章が刺さりやすくなります。

## 1-2. 各役者の責任を1行で

| 登場人物 | 一言で言うと |
|---|---|
| **WSGI/ASGI サーバ** | TCP ソケットと Python の橋渡し（生 HTTP → environ dict） |
| **WSGIHandler** | Django のリクエスト処理の最外殻。HttpRequest を作る |
| **Middleware** | リクエスト/レスポンスを **横断的に** 加工する玉ねぎの皮 |
| **URLconf** | パス文字列 → view 関数 への対応表 |
| **View** | リクエスト固有のロジックを実行し HttpResponse を作る |
| **Template** | HttpResponse の中身 (HTML) を作る道具 |
| **Model** | DB との橋渡し |

このドキュメントでは主に **Middleware** と **URLconf**、そして **HttpRequest / HttpResponse オブジェクト** を扱います（View / Template / Model は docs/02・03 で扱った）。

## ハンズオン 1: 全部のステップを実体験する

`uv run python manage.py runserver_plus --verbosity 3` を起動し、ブラウザで `/polls/` にアクセスしてみてください。CLI のログに以下が並ぶはずです：

1. SQL（`SELECT polls_question ...`）→ View 内のクエリ
2. アクセスログ（`127.0.0.1 - "GET /polls/ HTTP/1.1" 200`）→ WSGI サーバの出力

つまり「DB クエリ → レスポンス記録」という順序で実行されているのが分かります。本ドキュメントを通して、この間に挟まる中間処理（middleware や URL ルーティング）を見える化していきます。

---

# 第2章 HttpRequest オブジェクト

## 2-1. View が受け取る最初の引数

```python
def detail(request, question_id):
    ...
```

この `request` が `HttpRequest` インスタンスです。HTTP リクエストの内容を Python から触れる形に詰めた箱、と思ってください。

## 2-2. 必ず使う属性 (top 10)

| 属性 | 何が入る | 例 |
|---|---|---|
| `request.method` | HTTP メソッド | `"GET"` / `"POST"` / `"PUT"` |
| `request.path` | パス（クエリ除く） | `"/polls/1/"` |
| `request.GET` | クエリ文字列の辞書 (QueryDict) | `request.GET["page"]` |
| `request.POST` | POST フォームの辞書 (QueryDict) | `request.POST["choice"]` |
| `request.FILES` | アップロードファイルの辞書 | `request.FILES["cover"]` |
| `request.COOKIES` | クッキーの辞書 | `request.COOKIES["sessionid"]` |
| `request.headers` | HTTP ヘッダ（ケース無視） | `request.headers["User-Agent"]` |
| `request.META` | 環境変数（生）の辞書 | `request.META["REMOTE_ADDR"]` |
| `request.user` | 認証済みユーザー or `AnonymousUser` | `request.user.is_authenticated` |
| `request.session` | サーバ側セッション dict | `request.session["cart"]` |

`request.user` と `request.session` は **対応する middleware が有効** な場合だけ使えます（`AuthenticationMiddleware` / `SessionMiddleware`）。これは第10章で詳しく。

## 2-3. よく使うメソッド

```python
request.get_host()          # → "127.0.0.1:8000"
request.get_full_path()     # → "/polls/?page=2"  (クエリ含む)
request.build_absolute_uri()    # → "http://127.0.0.1:8000/polls/?page=2" (完全URL)
request.build_absolute_uri("/admin/")   # → "http://127.0.0.1:8000/admin/"
request.is_secure()         # HTTPS かどうか
```

特に `build_absolute_uri()` は **メールに URL を含めたい** ようなときに、テスト環境と本番でドメインが違っても自動で組み立ててくれて便利です。

## 2-4. QueryDict のクセ

`request.GET` と `request.POST` はただの dict ではなく **QueryDict** という特殊クラスです：

```python
# 同じキーが複数ある場合の挙動
# URL: /search/?tag=python&tag=django&tag=web

request.GET["tag"]            # "web" (最後の値だけ)
request.GET.get("tag", "")    # 同上
request.GET.getlist("tag")    # ["python", "django", "web"] (全部)
```

複数選択チェックボックスや「カンマ区切りタグ検索」では `getlist` を必ず使います。

## 2-5. `request.headers` と `request.META` の使い分け

`request.META` は WSGI の素の environ で、ヘッダ名は **`HTTP_USER_AGENT`** のように `HTTP_` プレフィックス + 大文字 + アンダースコア形式：

```python
request.META["HTTP_USER_AGENT"]
request.META["HTTP_X_REQUESTED_WITH"]
```

これは古い書き方。**新しいコードは `request.headers` を使うのが推奨** です：

```python
request.headers["User-Agent"]
request.headers["X-Requested-With"]
request.headers.get("HX-Request")    # 大小区別なし、ハイフン形式
```

`request.headers` はケース無視・ハイフン形式・dict ライクで読みやすく、本来 HTTP プロトコルが意図した書き方に近いです。

## ハンズオン 2: 自分のリクエストを覗くビュー

`polls` に `whoami` ビューを足して、自分のリクエストオブジェクトをそのまま表示するページを作ります。

### 1. ビューを書く

`polls/views.py` の末尾に追加：

```python
from django.http import JsonResponse


def whoami(request):
    """リクエスト内容を JSON で返すデバッグ用ビュー。"""
    return JsonResponse({
        "method": request.method,
        "path": request.path,
        "full_path": request.get_full_path(),
        "host": request.get_host(),
        "is_secure": request.is_secure(),
        "user_agent": request.headers.get("User-Agent", ""),
        "remote_addr": request.META.get("REMOTE_ADDR", ""),
        "query_params": dict(request.GET),
        "cookies": dict(request.COOKIES),
        "user_authenticated": request.user.is_authenticated,
        "session_key": request.session.session_key,
    })
```

`JsonResponse` は dict をそのまま JSON にしてくれる便利クラス。第3章でもう少し詳しく扱います。

### 2. URL を足す

`polls/urls.py`：

```python
urlpatterns = [
    path("", views.index, name="index"),
    path("whoami/", views.whoami, name="whoami"),    # ← 追加
    path("<int:question_id>/", views.detail, name="detail"),
    ...
]
```

**順序の注意**: `path("<int:question_id>/", ...)` の **前** に置く必要があります。逆にすると `whoami` の `w` が int としてパースできず 404 になる… ことはないですが（int converter は数字のみマッチ）、文字列ベースの URL の前にだけ来る一般則として覚えておいてください。

### 3. アクセスして観察

ブラウザで http://127.0.0.1:8000/polls/whoami/?page=2&tag=django にアクセス。整形済みの JSON が返ってきます：

```json
{
  "method": "GET",
  "path": "/polls/whoami/",
  "full_path": "/polls/whoami/?page=2&tag=django",
  "host": "127.0.0.1:8000",
  "is_secure": false,
  "user_agent": "Mozilla/5.0 ...",
  "remote_addr": "127.0.0.1",
  "query_params": {"page": ["2"], "tag": ["django"]},
  ...
}
```

`query_params` の値が **配列** になっているのが QueryDict の特徴です（複数値対応）。

---

# 第3章 HttpResponse オブジェクト

## 3-1. 基本: 文字列を返す

```python
from django.http import HttpResponse

def hello(request):
    return HttpResponse("こんにちは!")
```

これだけで「200 OK, Content-Type: text/html, 本文: こんにちは!」のレスポンスができます。

## 3-2. ステータスコードを変える

```python
return HttpResponse("Not Found", status=404)
return HttpResponse("Bad Request", status=400)
```

`status` を渡せば任意のコードに。Django は **代表的なエラーステータス用のサブクラス** も用意してくれています：

| クラス | コード | 用途 |
|---|---|---|
| `HttpResponse` | 200 | デフォルト |
| `HttpResponseRedirect(url)` | 302 | 一時リダイレクト |
| `HttpResponsePermanentRedirect(url)` | 301 | 恒久リダイレクト |
| `HttpResponseBadRequest` | 400 | 不正リクエスト |
| `HttpResponseForbidden` | 403 | 権限なし |
| `HttpResponseNotFound` | 404 | 見つからない |
| `HttpResponseNotAllowed(["GET"])` | 405 | メソッド不許可 |
| `HttpResponseGone` | 410 | リソース消滅 |
| `HttpResponseServerError` | 500 | サーバエラー |

通常は `HttpResponseRedirect` だけ手書きする機会があり、404 は `raise Http404` か `get_object_or_404` 経由で発生させる方が多いです。

## 3-3. JsonResponse — JSON を返す

```python
from django.http import JsonResponse

def api_list(request):
    return JsonResponse({"items": ["a", "b", "c"]})
```

dict 以外（list など）を渡したいときは `safe=False`：

```python
return JsonResponse([1, 2, 3], safe=False)
```

これは「dict 以外を JSON のトップレベルにすると JSON Hijacking 攻撃の余地がある」という昔の脆弱性対策で、明示的に許可させる仕組みになっています。

## 3-4. FileResponse — ファイルを返す

```python
from django.http import FileResponse

def download(request):
    return FileResponse(
        open("/path/to/file.pdf", "rb"),
        as_attachment=True,
        filename="report.pdf",
    )
```

`as_attachment=True` でブラウザに「ダウンロード扱い」させます（`Content-Disposition: attachment` ヘッダが付く）。

## 3-5. StreamingHttpResponse — 巨大データを少しずつ

CSV 100万行を生成して送る、というケースでメモリに全部展開せず流したいとき：

```python
from django.http import StreamingHttpResponse

def big_csv(request):
    def generator():
        yield "id,name\n"
        for row in Question.objects.iterator():
            yield f"{row.id},{row.question_text}\n"
    return StreamingHttpResponse(generator(), content_type="text/csv")
```

`yield` で1行ずつ返すと、その都度ソケットに書き込まれ、メモリ使用量が一定に保たれます。

## 3-6. ヘッダ・クッキーの操作

```python
response = HttpResponse("ok")

# ヘッダ
response["X-My-Header"] = "value"
response["Cache-Control"] = "no-cache"

# クッキー
response.set_cookie(
    "my_pref",
    "dark",
    max_age=3600,                # 秒
    httponly=True,               # JS から読めなくする
    secure=True,                 # HTTPS のみ
    samesite="Lax",              # CSRF 対策
)

# 削除
response.delete_cookie("my_pref")

return response
```

クッキーにユーザー識別など書く場合は **必ず `set_signed_cookie` で署名** すること：

```python
response.set_signed_cookie("user_id", "42", salt="user-cookie")

# 読む側
try:
    uid = request.get_signed_cookie("user_id", salt="user-cookie", max_age=3600)
except BadSignature:
    uid = None
```

これで「クッキーをユーザーに改竄されても署名検証で弾ける」状態になります。

## 3-7. `render()` は何をしている？

```python
return render(request, "polls/index.html", {"latest_question_list": ...})
```

これは以下と同じ：

```python
from django.template.loader import get_template
template = get_template("polls/index.html")
html = template.render({"latest_question_list": ...}, request)
return HttpResponse(html)
```

つまり `render` は **テンプレートをレンダリング → HttpResponse でラップ** するショートカット。`HttpResponse` の上位互換ではなく、内部で HttpResponse を作っているだけです。

## ハンズオン 3: いろんな Response を返す

`polls/views.py` の末尾に：

```python
from django.http import (
    HttpResponse,
    HttpResponseRedirect,
    HttpResponseNotFound,
    JsonResponse,
)


def response_demo(request):
    """?type=json / ?type=redirect / ?type=404 で挙動が変わる。"""
    response_type = request.GET.get("type", "html")

    if response_type == "json":
        return JsonResponse({"hello": "world", "items": [1, 2, 3]})

    if response_type == "redirect":
        return HttpResponseRedirect("/polls/")

    if response_type == "404":
        return HttpResponseNotFound("見つかりません")

    # デフォルト: HTML
    response = HttpResponse("<h1>Hello</h1>")
    response["X-Demo-Header"] = "yes"
    response.set_cookie("demo", "on", max_age=60)
    return response
```

`polls/urls.py` に：

```python
path("response-demo/", views.response_demo, name="response_demo"),
```

ブラウザで以下を順に試して挙動を確認：

| URL | 期待される挙動 |
|---|---|
| `/polls/response-demo/` | HTML + クッキー `demo=on` |
| `/polls/response-demo/?type=json` | JSON が返る |
| `/polls/response-demo/?type=redirect` | `/polls/` にリダイレクト |
| `/polls/response-demo/?type=404` | 404 ステータス |

開発者ツールの Network タブでステータスコード・ヘッダ・クッキーを確認できます。

---

# 第4章 URL Dispatcher の基本

## 4-1. `path()` の4引数

```python
path(route, view, kwargs=None, name=None)
```

| 引数 | 必須？ | 役割 |
|---|---|---|
| `route` | ✅ | URL パターン文字列（例: `"<int:year>/"`） |
| `view` | ✅ | ビュー関数 or `View.as_view()` |
| `kwargs` | 任意 | view に **追加で渡す** キーワード引数 |
| `name` | 任意 | URL 逆引き用の名前 |

`kwargs` で view に値を「埋め込む」ことができます：

```python
path("blog/", views.list_posts, {"category": "tech"}, name="tech-posts"),
path("news/", views.list_posts, {"category": "news"}, name="news-posts"),

# view 側
def list_posts(request, category):
    ...
```

同じ view で **URL ごとに渡す値を変える** ことができる小技です。

## 4-2. URL マッチングのルール

1. `ROOT_URLCONF` から始まる（このリポジトリは `config.urls`）
2. `urlpatterns` を **上から順** に試す
3. 最初にマッチしたパターンで止まる
4. クエリ文字列（`?key=value`）と HTTP メソッドは **無視** される
5. パスはホスト・ポート部を除いた `path_info` 部分のみ

「クエリと HTTP メソッドが無視される」は最初引っかかりやすい点です。`GET` も `POST` も同じ URL パターンを通ります。`request.method` でビュー内で分岐する設計です：

```python
def login(request):
    if request.method == "POST":
        # 認証処理
        ...
    else:
        # フォーム表示
        ...
```

## 4-3. `include()` で URLconf をネスト

```python
# config/urls.py
urlpatterns = [
    path("admin/", admin.site.urls),
    path("polls/", include("polls.urls", namespace="polls")),
    path("todo/", include("todo.urls", namespace="todo")),
]
```

`/polls/1/` というリクエストが来ると：

1. `config.urls` で `"polls/"` にマッチ → 残り `"1/"` を `polls.urls` へ
2. `polls.urls` で `"<int:question_id>/"` にマッチ → `question_id=1`
3. `polls.views.detail(request, question_id=1)` が呼ばれる

include は **そこまでの prefix を URL から削除して残りを渡す** イメージ。

## 4-4. `APPEND_SLASH` の罠

Django のデフォルトでは「末尾にスラッシュなしの URL は、スラッシュ付き URL にリダイレクト」されます：

```
GET /polls    →  301 → /polls/
```

これは `CommonMiddleware` が `APPEND_SLASH=True`（デフォルト）のときに行う処理。`urlpatterns` の側では **末尾スラッシュ付きで書く** のがコミュニティの慣習です。

例外: API エンドポイントなどでスラッシュなしを許容したいときは `APPEND_SLASH = False` にする手もありますが、その場合は両方の path を明示的に書く必要があります。

## ハンズオン 4: URL を観察する

`uv run python manage.py show_urls` を打ってみてください（`django-extensions` 経由）。プロジェクトで有効な全 URL が一覧できます：

```
/admin/              admin.site.urls
/polls/              polls.views.index               polls:index
/polls/whoami/       polls.views.whoami              polls:whoami
/polls/<question_id>/  polls.views.detail            polls:detail
/polls/<question_id>/results/    polls.views.results polls:results
/polls/<question_id>/vote/       polls.views.vote    polls:vote
...
```

このコマンドは「あれ、この URL ってどこに登録したっけ？」と迷ったときの最強デバッグツールです。

---

# 第5章 ビルトインのパスコンバータ

## 5-1. `<converter:name>` の構文

```python
path("articles/<int:year>/", views.year_archive)
```

`<int:year>` が **「URL のこの位置に整数があったら、`year` という名前のキーワード引数として view に渡す」** という意味です。

ビルトインコンバータは5種類：

| Converter | マッチ | 戻り値の型 | 例 URL |
|---|---|---|---|
| `str` | `/` を含まない任意文字列（デフォルト） | `str` | `<str:slug>` |
| `int` | 0 以上の整数 | `int` | `<int:year>` |
| `slug` | ASCII 英数 + `-` + `_` | `str` | `<slug:slug>` |
| `uuid` | UUID 形式（小文字 + ハイフン） | `uuid.UUID` | `<uuid:id>` |
| `path` | `/` を含む任意文字列 | `str` | `<path:rest>` |

## 5-2. 型変換の意味

`<int:year>` を書くと、`view(request, year)` の `year` が **すでに `int` 型** になっています。

```python
path("year/<int:year>/", views.year_view)

def year_view(request, year):
    # year は int。"2024" ではなく 2024
    next_year = year + 1
    return HttpResponse(f"翌年は {next_year}")
```

URL から手で `int(request.path_params...)` する必要がないのがミソ。

## 5-3. `slug` vs `str` の違い

両方とも文字列ですが：

| | `str` | `slug` |
|---|---|---|
| マッチ | `/` 以外のあらゆる文字 | 英数 + `-` + `_` のみ |
| 例: マッチ | `hello world`、`日本語`、`abc-123` | `abc-123`、`hello_world` |
| 例: マッチしない | `path/with/slashes` | `hello world`（スペース）、`日本語` |

ブログ記事の URL のように **SEO 用に整形済みの文字列を期待** する場合は `slug` を使うと、想定外の入力を URL 段階で弾けます。

## 5-4. `path` の特殊性

```python
path("files/<path:filepath>/", views.serve)
```

`<path:filepath>` は `/` を含んだまま全部マッチします：

```
/files/docs/2024/report.pdf/  →  filepath="docs/2024/report.pdf"
```

ファイルブラウザのような **任意の階層を URL に乗せたい** ケースで使います。**多用するとパターンマッチが曖昧になりやすい** ので、最後の方の path() に書くのが慣習。

## 5-5. `uuid` の使い所

公開 URL に `?id=42` のような連番 ID を出すと「全件取られる」「次の ID を推測できる」など困るケース。代わりに UUID にすると：

```python
path("session/<uuid:token>/", views.session_view)

# URL 例
/session/f0f0a3e6-...-c4d8a5e7/
```

ID を推測できなくなります。モデル側で `UUIDField(default=uuid.uuid4)` を主キーや一意フィールドにしておく組み合わせ。

## ハンズオン 5: コンバータを観察する

`polls/views.py` の末尾に：

```python
def converter_demo(request, value):
    return HttpResponse(f"受け取った値: {value!r} (型: {type(value).__name__})")
```

`polls/urls.py` に4種類のパターンを並列に登録：

```python
urlpatterns = [
    ...
    path("conv/str/<str:value>/", views.converter_demo, name="conv-str"),
    path("conv/int/<int:value>/", views.converter_demo, name="conv-int"),
    path("conv/slug/<slug:value>/", views.converter_demo, name="conv-slug"),
    path("conv/uuid/<uuid:value>/", views.converter_demo, name="conv-uuid"),
]
```

ブラウザで以下を順番に：

| URL | 結果 |
|---|---|
| `/polls/conv/str/hello/` | `'hello' (型: str)` |
| `/polls/conv/int/42/` | `42 (型: int)` |
| `/polls/conv/int/abc/` | 404（int に変換できない） |
| `/polls/conv/slug/my-post/` | `'my-post' (型: str)` |
| `/polls/conv/slug/has space/` | 404（slug にスペースはダメ） |
| `/polls/conv/uuid/f0f0a3e6-c4f0-4d8e-a5b1-c4d8a5e7b3a1/` | `UUID('...') (型: UUID)` |
| `/polls/conv/uuid/not-a-uuid/` | 404 |

URL の **検証が自動で効いている** こと、view に渡るときには **すでに目的の型** になっていることが体感できます。

---

# 第6章 カスタムパスコンバータ

## 6-1. なぜ必要？

ビルトインで足りないケース：
- 「`chef` / `gourmand` / `foodie` のいずれかだけ」を URL で受けたい
- 「`YYYY-MM-DD` 形式の日付」を `date` オブジェクトで受け取りたい
- 「2桁の年（`24` で 2024 年）」を扱いたい

これらは **カスタムコンバータ** を書けば 1 か所で完結できます。

## 6-2. コンバータクラスの3要素

```python
class FourDigitYearConverter:
    regex = r"[0-9]{4}"

    def to_python(self, value):
        return int(value)

    def to_url(self, value):
        return f"{value:04d}"
```

| 要素 | 役割 |
|---|---|
| `regex` | URL にマッチさせる正規表現（先頭 `^` / 末尾 `$` 不要） |
| `to_python(value)` | URL から取り出した文字列を view に渡す前に Python 型に変換 |
| `to_url(value)` | `reverse()` で URL を組み立てるとき Python 型 → 文字列に逆変換 |

## 6-3. 登録と使用

```python
from django.urls import path, register_converter
from . import converters

register_converter(converters.FourDigitYearConverter, "yyyy")

urlpatterns = [
    path("articles/<yyyy:year>/", views.year_archive),
]
```

`register_converter(クラス, "登録名")` で名前を付け、URL パターンの `<...:...>` の前半に書きます。

## 6-4. 例: 日付コンバータ

`YYYY-MM-DD` 形式を `datetime.date` で受け取るコンバータ：

```python
import datetime


class IsoDateConverter:
    regex = r"\d{4}-\d{2}-\d{2}"

    def to_python(self, value):
        return datetime.date.fromisoformat(value)

    def to_url(self, value):
        return value.isoformat()
```

```python
# urls.py
register_converter(IsoDateConverter, "isodate")

urlpatterns = [
    path("by-date/<isodate:day>/", views.by_date, name="by-date"),
]

# views.py
def by_date(request, day):
    # day はすでに date オブジェクト
    questions = Question.objects.filter(pub_date__date=day)
    return render(request, "polls/by_date.html", {"day": day, "questions": questions})
```

「URL に `/by-date/2026-05-16/` と書けば、view では `day=date(2026, 5, 16)` を受け取る」となり、view 側のパースコードがゼロになります。

## 6-5. 例: enum (固定リスト) コンバータ

`chef` / `gourmand` / `foodie` のいずれかだけ受け付ける：

```python
from enum import StrEnum


class Role(StrEnum):
    CHEF = "chef"
    GOURMAND = "gourmand"
    FOODIE = "foodie"


class RoleConverter:
    regex = "|".join(r.value for r in Role)

    def to_python(self, value):
        return Role(value)

    def to_url(self, value):
        if isinstance(value, Role):
            return value.value
        if value in Role._value2member_map_:
            return value
        raise ValueError(f"{value!r} is not a valid Role")
```

これだけで `/role/chef/` `/role/gourmand/` `/role/foodie/` の3つだけ通り、それ以外は 404 になります。`view(request, role)` の `role` は `Role` enum 型として受け取れます。

## ハンズオン 6: 日付コンバータを polls に組み込む

### 1. converters.py を新規作成

`polls/converters.py`：

```python
import datetime


class IsoDateConverter:
    """YYYY-MM-DD 形式の文字列を date に変換する path converter。"""

    regex = r"\d{4}-\d{2}-\d{2}"

    def to_python(self, value):
        return datetime.date.fromisoformat(value)

    def to_url(self, value):
        return value.isoformat()
```

### 2. urls.py で登録

`polls/urls.py` の先頭に：

```python
from django.urls import path, register_converter
from . import converters, views

register_converter(converters.IsoDateConverter, "isodate")

app_name = "polls"
urlpatterns = [
    ...
    path("by-date/<isodate:day>/", views.by_date, name="by_date"),
]
```

### 3. view を追加

`polls/views.py`：

```python
def by_date(request, day):
    questions = Question.objects.filter(pub_date__date=day).order_by("-pub_date")
    return render(
        request,
        "polls/by_date.html",
        {"day": day, "questions": questions},
    )
```

### 4. テンプレートを作成

`polls/templates/polls/by_date.html`：

```django
{% extends "polls/base.html" %}

{% block title %}{{ day|date:"Y-m-d" }} の質問{% endblock %}

{% block content %}
    <h2>{{ day|date:"Y年n月j日" }} の質問</h2>
    <ul>
        {% for q in questions %}
            <li><a href="{% url 'polls:detail' q.id %}">{{ q.question_text }}</a></li>
        {% empty %}
            <li>この日の質問はありません。</li>
        {% endfor %}
    </ul>
    <p><a href="{% url 'polls:index' %}">一覧に戻る</a></p>
{% endblock %}
```

### 5. 動作確認

ブラウザで `http://127.0.0.1:8000/polls/by-date/2026-05-16/`（今日の日付）と、存在しない日付 `2024-01-01` を試して、内容が変わることを確認。

そして `/polls/by-date/abc/` のような壊れた URL は **404 になり、view にすら到達しない** ことも確認してください。これがコンバータの「**URL レベルで型検証する**」威力です。

---

# 第7章 `re_path` で正規表現を使う

## 7-1. `path` で足りないケース

`path()` のパスコンバータは便利ですが、たとえば「**2桁または4桁の年**」のような **複雑な正規表現** は表現できません。そういうときは `re_path()` の出番です：

```python
from django.urls import re_path

urlpatterns = [
    re_path(r"^articles/(?P<year>\d{2}|\d{4})/$", views.year_archive),
]
```

| | `path()` | `re_path()` |
|---|---|---|
| 構文 | `<int:year>` | `(?P<year>\d{4})` |
| 学習コスト | 低 | 正規表現の知識が必要 |
| 表現力 | コンバータ + ビルトイン型 | 任意の正規表現 |
| 推奨 | **基本これ** | パスコンバータでは無理なとき |

Django 2.0 以降は `path()` が主役。`re_path` は補助に回りました。

## 7-2. 名前付きグループ

```python
re_path(r"^articles/(?P<year>\d{4})/$", views.year_archive)
```

- `(?P<year>...)` → 名前付きキャプチャ。`year` という名前で view に渡る
- 名前を付けない `(...)` も使えますが、**順序依存** で壊れやすいので **必ず名前付きを使う** こと

## 7-3. 先頭の `^` と末尾の `$`

`re_path` のパターンには **`^`（先頭）と `$`（末尾）** を明示することが多いです：

```python
re_path(r"^articles/(?P<year>\d{4})/$", ...)
```

これがないと「URL の途中で `articles/` を含むもの」全てにマッチしてしまうケースが出ます。include されたサブ URLconf の場合は先頭の `^` を省略するパターンもあります（include した側が prefix を取り除いて渡してくるので）。

## 7-4. 型変換は手動

`path()` と違い、`re_path` は **キャプチャした値は常に str** です。`int(year)` のような変換は view 側で：

```python
def year_archive(request, year):
    year = int(year)   # 文字列から手動変換が必要
    ...
```

これも `path()` が推奨される理由の1つ。

## ハンズオン 7: 月＋年の組み合わせを `re_path` で表現

`/polls/by-month/2026-05/` のように **YYYY-MM 形式** を受け取りたい場合。`path` のビルトインコンバータでは無理なので `re_path` で書きます：

```python
# polls/urls.py
from django.urls import re_path

urlpatterns = [
    ...
    re_path(
        r"^by-month/(?P<year>\d{4})-(?P<month>\d{2})/$",
        views.by_month,
        name="by_month",
    ),
]
```

```python
# polls/views.py
def by_month(request, year, month):
    year, month = int(year), int(month)
    questions = Question.objects.filter(
        pub_date__year=year,
        pub_date__month=month,
    )
    return render(
        request,
        "polls/by_date.html",
        {"day": datetime.date(year, month, 1), "questions": questions},
    )
```

ブラウザで `/polls/by-month/2026-05/` を開けば、その月の質問だけ。`/polls/by-month/26-5/` は **マッチしない** ので 404 — `\d{4}-\d{2}` という正規表現が4桁-2桁を強制している証拠です。

> **どっちで書く？**: 同じことは「カスタムパスコンバータで YearMonthConverter を書く」のでも実現できます。`re_path` は **その場限りで使う特殊パターン** に、カスタムコンバータは **複数の URL で再利用したい型** に、と使い分けるのがおすすめ。

---

# 第8章 名前付き URL と reverse

## 8-1. URL をハードコードしない

テンプレートやコードに `/polls/1/` のような URL を直接書くと、後で URL 構造を変えたときに **書き換え漏れ** が必ず起きます。Django は URL に **名前** を付けて、コードからは名前経由で参照する仕組みを推奨しています：

```python
# urls.py
path("<int:question_id>/", views.detail, name="detail"),
```

```django
{# テンプレート #}
<a href="{% url 'polls:detail' question.id %}">詳細</a>
```

```python
# Python コード
from django.urls import reverse
url = reverse("polls:detail", args=[question.id])
```

URL のパス文字列を変えても **コード側は無修正で済む** のがメリット。

## 8-2. `{% url %}` テンプレートタグ

```django
{# 位置引数 #}
<a href="{% url 'polls:detail' question.id %}">詳細</a>

{# キーワード引数 #}
<a href="{% url 'polls:detail' question_id=question.id %}">詳細</a>

{# 名前を変数に格納 (as) #}
{% url 'polls:index' as index_url %}
<a href="{{ index_url }}">一覧</a>
```

`{% url %}` は **マッチする URL が見つからないと** `NoReverseMatch` で 500 エラーになります。テストで早期に発見しやすいのが利点。

## 8-3. `reverse()` 関数

```python
from django.urls import reverse

# 位置引数
url = reverse("polls:detail", args=[1])

# キーワード引数
url = reverse("polls:detail", kwargs={"question_id": 1})

# クエリ文字列を付けたい場合は手で
url = reverse("polls:index") + "?page=2"
```

ビューのリダイレクトでよく使う：

```python
from django.http import HttpResponseRedirect
from django.urls import reverse

def vote(request, question_id):
    ...
    return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))
```

## 8-4. `get_absolute_url()` パターン

モデルに **「このオブジェクトの URL」** を返すメソッドを生やすのが Django の慣習：

```python
# polls/models.py
from django.urls import reverse

class Question(models.Model):
    ...

    def get_absolute_url(self):
        return reverse("polls:detail", args=[self.pk])
```

すると：

```django
{# テンプレートで自動的に使える #}
<a href="{{ question.get_absolute_url }}">{{ question.question_text }}</a>
```

`get_absolute_url()` を実装すると、Django admin の「サイトで表示」ボタンも自動で有効になります。**モデルクラスを書いたら必ず付ける** くらいに思っていて OK。

## 8-5. `redirect()` ショートカット

リダイレクトは `redirect()` を使うと短く書けます：

```python
from django.shortcuts import redirect

# 以下の4種類どれでも書ける:
return redirect("polls:results", question.id)          # 名前付き URL
return redirect(reverse("polls:results", args=[1]))    # URL 文字列
return redirect(question)                              # get_absolute_url() を使う
return redirect("/polls/")                             # 直接 URL
```

「`return redirect(question)`」は `Question` モデルに `get_absolute_url()` があれば自動で呼ばれます。短く書けて読みやすい。

## ハンズオン 8: `get_absolute_url` を入れる

### 1. モデルに追加

`polls/models.py`：

```python
from django.urls import reverse


class Question(models.Model):
    ...

    def get_absolute_url(self):
        return reverse("polls:detail", args=[self.pk])
```

### 2. テンプレートを書き換え

`polls/templates/polls/_question_item.html` の `{% url 'polls:detail' question.id %}` を `{{ question.get_absolute_url }}` に置き換え：

```django
<li>
    {% if question.cover_image %}
        <img src="{{ question.cover_image.url }}" alt="" style="height: 2em; vertical-align: middle;">
    {% endif %}
    <a href="{{ question.get_absolute_url }}">{{ question.question_text }}</a>
    <small>（{{ question.pub_date|date:"Y-m-d" }} 公開）</small>
</li>
```

### 3. views の redirect も簡素化

`polls/views.py`：

```python
from django.shortcuts import redirect

def vote(request, question_id):
    ...
    return redirect("polls:results", question.id)
```

### 4. admin で「サイトで表示」が出ているか

`/admin/polls/question/1/change/` を開くと、右上に「**サイトで表示**」ボタン（→マークアイコン）が出ているはず。これは `get_absolute_url` を実装したアプリだけに現れる機能。

---

# 第9章 URL 名前空間

## 9-1. なぜ名前空間が必要？

仮に `polls` と `todo` の両方に `name="index"` の URL があったら：

```python
# polls/urls.py
path("", views.index, name="index")

# todo/urls.py
path("", views.index, name="index")
```

```python
reverse("index")    # ← どっちの index？
```

Django には **後勝ち** の挙動があるので「最後に登録された方が勝つ」状態になります。これは事故の元。

そこで **名前空間** で「polls の index」「todo の index」と区別します：

```python
reverse("polls:index")    # → /polls/
reverse("todo:index")     # → /todo/
```

## 9-2. 設定の2点

1. **アプリ側** `urls.py` で `app_name = "polls"` を宣言
2. **プロジェクト側** `urls.py` で `include("polls.urls", namespace="polls")` と include

```python
# polls/urls.py
app_name = "polls"

urlpatterns = [
    path("", views.index, name="index"),
    ...
]
```

```python
# config/urls.py
urlpatterns = [
    path("polls/", include("polls.urls", namespace="polls")),
    path("todo/", include("todo.urls", namespace="todo")),
]
```

> **慣習**: `app_name` と `namespace` は普通同じ名前にします。違う名前にできるのは「**同じアプリを2回 include したい**」ケースのため（次節）。

## 9-3. 同じアプリを複数インスタンス化

たとえば polls アプリを「会社版」と「個人版」で別 URL に2回設置したいとき：

```python
# config/urls.py
urlpatterns = [
    path("company-polls/", include("polls.urls", namespace="company")),
    path("personal-polls/", include("polls.urls", namespace="personal")),
]
```

```python
reverse("company:detail", args=[1])    # → /company-polls/1/
reverse("personal:detail", args=[1])   # → /personal-polls/1/
```

`app_name` は1つでも、`namespace=` が複数のインスタンスを区別します。

## 9-4. ネストした名前空間

```python
# config/urls.py
urlpatterns = [
    path("api/v1/", include("api.urls", namespace="v1")),
    path("api/v2/", include("api.urls", namespace="v2")),
]

# api/urls.py
app_name = "api"
urlpatterns = [
    path("posts/", include("posts.urls", namespace="posts")),
]

# posts/urls.py
app_name = "posts"
urlpatterns = [
    path("<int:pk>/", views.detail, name="detail"),
]
```

```python
reverse("v1:posts:detail", args=[1])    # → /api/v1/posts/1/
reverse("v2:posts:detail", args=[1])    # → /api/v2/posts/1/
```

API のバージョニングなどでよく使うパターン。

---

# 第10章 ミドルウェア

## 10-1. ミドルウェアって何？

すでに「玉ねぎの皮」と紹介しましたが、改めて図にすると：

```
リクエスト                                        レスポンス
   │                                                ▲
   ▼                                                │
[SecurityMiddleware]    ──→        ←──    [SecurityMiddleware]
   │                                                ▲
   ▼                                                │
[SessionMiddleware]     ──→        ←──    [SessionMiddleware]
   │                                                ▲
   ▼                                                │
[CsrfViewMiddleware]    ──→        ←──    [CsrfViewMiddleware]
   │                                                ▲
   ▼                                                │
[AuthenticationMiddleware] ─→    ←─ [AuthenticationMiddleware]
   │                                                ▲
   ▼                                                │
        View 関数 (DB アクセス、テンプレート描画...)
```

リクエストは **上から下** に通り、レスポンスは **下から上** に戻ります。各層が `request` と `response` を加工できる：

- `SessionMiddleware` は **行きで** `request.session` を生やす
- `CsrfViewMiddleware` は **行きで** CSRF トークンを検証
- `AuthenticationMiddleware` は **行きで** `request.user` を生やす
- `MessageMiddleware` は **帰りで** flash メッセージを保存

## 10-2. 標準ミドルウェアの責任分担

`config/settings.py` のデフォルト：

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
```

| 名前 | 役割 |
|---|---|
| `SecurityMiddleware` | HSTS / SSL リダイレクト / `X-Content-Type-Options: nosniff` などのセキュリティ HTTP ヘッダ付与 |
| `SessionMiddleware` | `request.session` を生やす |
| `CommonMiddleware` | `APPEND_SLASH` の処理、`PREPEND_WWW`、`User-Agent` ブロックなど |
| `CsrfViewMiddleware` | POST フォームの CSRF トークン検証 |
| `AuthenticationMiddleware` | session から `user` を復元して `request.user` に設定 |
| `MessageMiddleware` | `messages.success(...)` のような一時メッセージ機能 |
| `XFrameOptionsMiddleware` | `X-Frame-Options: DENY` を付け Clickjacking 防止 |

## 10-3. 順序が大事

`AuthenticationMiddleware` は `request.session` を読みに行くので、`SessionMiddleware` が **前** にないと動きません。そういう依存関係が暗黙にあります。

迷ったら **デフォルトの順序を崩さない** こと。自前のミドルウェアは、最後（または特定の標準ミドルウェアの隣）に挿入します。

## 10-4. 関数型ミドルウェアの書き方

最小形：

```python
def simple_middleware(get_response):
    # サーバ起動時に1回だけ実行 (init 部分)
    def middleware(request):
        # 行きの処理 (view の前)

        response = get_response(request)    # 次のレイヤーに進む

        # 帰りの処理 (view の後)
        return response

    return middleware
```

「外側の `simple_middleware(get_response)`」は **1回だけ呼ばれる** 初期化のため。「内側の `middleware(request)`」が **リクエストごとに呼ばれる**。

## 10-5. クラス型ミドルウェアの書き方

```python
class SimpleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 行きの処理

        response = self.get_response(request)

        # 帰りの処理
        return response
```

どちらでも書けます。状態を持たせたいなら class、シンプルなら関数。

## 10-6. ショートサーキット（途中で打ち切る）

途中の middleware で `response` を return してしまうと、**それより内側の middleware と view は実行されません**：

```python
def block_admin(get_response):
    def middleware(request):
        if request.path.startswith("/admin/") and not request.user.is_staff:
            return HttpResponse("Forbidden", status=403)   # ここで終わり
        return get_response(request)
    return middleware
```

`SecurityMiddleware` の HTTPS 強制リダイレクトなどがこのパターン。

## 10-7. フックメソッド（クラス型のとき）

クラス型ミドルウェアには `__call__` のほかに以下のメソッドが定義できます：

| メソッド | タイミング | 用途 |
|---|---|---|
| `process_view(request, view_func, view_args, view_kwargs)` | view 呼び出し直前 | 認可チェック、view の差し替え |
| `process_exception(request, exception)` | view で例外発生時 | 例外を捕まえてカスタムレスポンス |
| `process_template_response(request, response)` | TemplateResponse 返却時 | テンプレートやコンテキストの加工 |

`process_view` の例：

```python
class StaffOnlyAdmin:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.path.startswith("/admin/") and not request.user.is_staff:
            return HttpResponse("Forbidden", status=403)
        return None    # None を返すと「特に何もせず続行」
```

## 10-8. 自前ミドルウェアの典型例

### 例1: リクエスト処理時間をログに出す

```python
# config/middleware.py
import time
import logging

logger = logging.getLogger(__name__)


def timing_middleware(get_response):
    def middleware(request):
        start = time.monotonic()
        response = get_response(request)
        duration = (time.monotonic() - start) * 1000
        logger.info(f"{request.method} {request.path} → {response.status_code} ({duration:.1f}ms)")
        return response
    return middleware
```

### 例2: リクエスト ID をヘッダに付与

```python
import uuid


def request_id_middleware(get_response):
    def middleware(request):
        request.id = uuid.uuid4().hex[:12]
        response = get_response(request)
        response["X-Request-Id"] = request.id
        return response
    return middleware
```

`request.id` は view 内でログ出力時に使うと、各リクエストを追跡できます。

### 例3: HTMX 判定

```python
def htmx_middleware(get_response):
    def middleware(request):
        request.is_htmx = request.headers.get("HX-Request") == "true"
        return get_response(request)
    return middleware
```

view 側で `if request.is_htmx:` と書けるようになります。

## 10-9. 登録

```python
# config/settings.py
MIDDLEWARE = [
    ...
    "config.middleware.timing_middleware",
    "config.middleware.request_id_middleware",
]
```

文字列で **Python の import パス** を書きます。

## ハンズオン 10: リクエスト ID + 処理時間ミドルウェアを足す

### 1. ミドルウェアモジュールを作成

`config/middleware.py` を新規作成：

```python
import logging
import time
import uuid

logger = logging.getLogger(__name__)


def request_id_middleware(get_response):
    """各リクエストに ID を発番し、X-Request-Id レスポンスヘッダで返す。"""

    def middleware(request):
        request.id = uuid.uuid4().hex[:12]
        response = get_response(request)
        response["X-Request-Id"] = request.id
        return response

    return middleware


def timing_middleware(get_response):
    """リクエスト処理時間を計測してログに出す。"""

    def middleware(request):
        start = time.monotonic()
        response = get_response(request)
        duration_ms = (time.monotonic() - start) * 1000
        logger.info(
            "[%s] %s %s -> %s (%.1fms)",
            getattr(request, "id", "?"),
            request.method,
            request.path,
            response.status_code,
            duration_ms,
        )
        return response

    return middleware
```

### 2. MIDDLEWARE に登録

`config/settings.py`：

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "config.middleware.request_id_middleware",       # ← 追加
    "config.middleware.timing_middleware",           # ← 追加
]
```

順序は重要です。`request_id_middleware` を **`timing_middleware` より前** に置くことで、`timing_middleware` のログに request id が載るようになります。

### 3. 動作確認

ブラウザで `/polls/` を開いて、開発者ツール → Network → レスポンスヘッダに：

```
X-Request-Id: 7c2b9e4a8d1f
```

のような値が付いていれば成功。CLI のログにも：

```
[7c2b9e4a8d1f] GET /polls/ -> 200 (12.3ms)
```

が出るはず。

### 4. ログを設定でつなぎ込む

このリポジトリの `config/settings.py` の LOGGING は `django.db.backends` だけを拾う設定です。`config.middleware` のログも CLI に出したいなら、`loggers` を1つ足します：

```python
LOGGING = {
    ...
    "loggers": {
        "django.db.backends": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "config.middleware": {                     # ← 追加
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
```

これで `timing_middleware` のログ行が CLI に流れます。

---

# 第11章 ハンドラ404 と例外処理

## 11-1. カスタム404ページ

`DEBUG=True` のときは Django 標準の 404 デバッグページが出ますが、`DEBUG=False` にすると **白い「Not Found」が出るだけ** です。テンプレートを用意すれば自前のページに差し替えできます：

### 1. テンプレートを置く

`templates/404.html`（プロジェクト直下の templates ディレクトリに）：

```django
<!DOCTYPE html>
<html lang="ja">
<head><title>ページが見つかりません</title></head>
<body>
    <h1>404: お探しのページが見つかりません</h1>
    <p>パス: {{ request.path }}</p>
    <p><a href="/">ホームに戻る</a></p>
</body>
</html>
```

### 2. settings の TEMPLATES.DIRS にプロジェクト共通テンプレート用ディレクトリを追加

```python
TEMPLATES = [
    {
        ...
        "DIRS": [BASE_DIR / "templates"],
        ...
    },
]
```

### 3. DEBUG=False で確認

```python
DEBUG = False
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
```

存在しない URL を叩くとカスタム 404 が出るはず。確認後 `DEBUG=True` に戻すのを忘れずに。

`handler500` / `handler403` / `handler400` も同様にカスタマイズできます。

## 11-2. `raise Http404` の使い方

view 内で「ここでもう 404」とした方が見通しがいいことが多いです：

```python
from django.http import Http404

def detail(request, question_id):
    try:
        question = Question.objects.get(pk=question_id)
    except Question.DoesNotExist:
        raise Http404("質問が見つかりません")
    ...
```

このコードと等価なのが `get_object_or_404`：

```python
from django.shortcuts import get_object_or_404

def detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    ...
```

ほぼ常に後者を使います。

---

# 付録 A: ステータスコード早見表

| コード | 名前 | 用途 |
|---|---|---|
| 200 | OK | 通常成功 |
| 201 | Created | リソース作成成功（API 用） |
| 204 | No Content | 成功だが返す本文なし |
| 301 | Moved Permanently | 恒久リダイレクト（SEO 維持） |
| 302 | Found | 一時リダイレクト（POST 後の Redirect-Get パターン） |
| 304 | Not Modified | キャッシュ有効 |
| 400 | Bad Request | クライアントが間違ったリクエスト |
| 401 | Unauthorized | 未認証 |
| 403 | Forbidden | 認証はあるが権限なし |
| 404 | Not Found | リソースなし |
| 405 | Method Not Allowed | GET は OK だが POST はダメ など |
| 410 | Gone | かつてあったが消えた |
| 500 | Internal Server Error | サーバ側のバグ |
| 502 | Bad Gateway | 上流のサーバが応答しない |
| 503 | Service Unavailable | 一時停止中 |

---

# 付録 B: コマンド・テンプレート早見

## URL を確認

```bash
uv run python manage.py show_urls
```

## reverse をシェルで試す

```bash
uv run python manage.py shell_plus
```

```python
>>> from django.urls import reverse
>>> reverse("polls:detail", args=[1])
'/polls/1/'
>>> reverse("polls:detail", kwargs={"question_id": 1})
'/polls/1/'
```

## カスタムコンバータ登録パターン

```python
# myapp/converters.py
class FooConverter:
    regex = r"..."
    def to_python(self, value): return ...
    def to_url(self, value): return ...

# myapp/urls.py
from django.urls import register_converter
from . import converters, views

register_converter(converters.FooConverter, "foo")

urlpatterns = [path("<foo:x>/", views.bar)]
```

## ミドルウェアのスケルトン

```python
def my_middleware(get_response):
    def middleware(request):
        # 行き
        response = get_response(request)
        # 帰り
        return response
    return middleware
```

---

# 付録 C: よくあるハマりどころ

| 症状 | 原因 | 対処 |
|---|---|---|
| `NoReverseMatch` | URL に引数が足りない / 多い / 名前ミス | `show_urls` で実際の name を確認 |
| `404 で view に到達しない` | `path()` のパターンや converter が違う | パターンを `show_urls` で確認、コンバータの regex を確認 |
| `request.session` で `AttributeError` | `SessionMiddleware` が無効 | `MIDDLEWARE` にあるか確認 |
| `request.user` が常に AnonymousUser | `AuthenticationMiddleware` 無効 | 同上 |
| CSRF 失敗 | テンプレに `{% csrf_token %}` 忘れ / cookie 削除 | 入れる、ブラウザクッキー削除 |
| `APPEND_SLASH` の挙動が分からない | `CommonMiddleware` が自動リダイレクト | `urls.py` を末尾スラッシュ付きに統一 |
| 自作 middleware が呼ばれない | `MIDDLEWARE` への登録忘れ / import パスミス | `settings.py` を再確認、起動エラーが出てないか確認 |
| `path()` で `<str:x>` がスラッシュ含む URL にマッチしない | str converter の仕様 | スラッシュを含めたいなら `path` converter を使う |

---

# 付録 D: 参考リンク

- [Request and response objects](https://docs.djangoproject.com/en/6.0/ref/request-response/) — 公式リファレンス
- [URL dispatcher](https://docs.djangoproject.com/en/6.0/topics/http/urls/) — 公式
- [Middleware](https://docs.djangoproject.com/en/6.0/topics/http/middleware/) — 公式
- [Custom URL path converter — adamj.eu](https://adamj.eu/tech/2025/08/01/django-custom-url-converter-string/)
- [Django Request-Response Cycle — Medium](https://medium.com/@developerstacks/django-request-response-cycle-7165167f54c5)
- [Django Request Life Cycle Explained — DEV](https://dev.to/nilebits/django-request-life-cycle-explained-ci6)

---

ここまで完走おつかれさまでした。「ブラウザがクリックされてから HTML が返ってくる」一連の流れを **コードの目線で追える** ようになったはずです。次は **フォーム / 認証 / Admin の深掘り** あたりに進むと、ここで覚えた `request.POST` `request.user` `CsrfViewMiddleware` が本格的に活きてきます。
