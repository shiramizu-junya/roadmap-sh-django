# manage.py と URL ルーティング 完全入門

> **このドキュメントの読み方**
> 上から順に読み、コードブロックに出てくる手順を実行していけば、Django の `manage.py` と URL ルーティング (URLconf) を実務レベルで使えるようになります。
> 教材内に **「ハンズオン」** のセクションが何度か出てきます。各ハンズオンは前のハンズオンの結果を使って育てていく形なので、上から順番にやってください。
> 完走すると、すでに作成済みの `polls/` アプリが「投票アプリ」として動く状態になります。

---

## このドキュメントで作るもの

すでにプロジェクトには:
- `config/` — 設定パッケージ
- `todo/` — TODO アプリ（実装済み）
- `polls/` — 投票アプリ（**雛形だけある**。これから育てる）

があります。本ドキュメントを完走すると `polls/` がこんな URL 構成で動きます:

```
/polls/                       一覧（質問のリスト）
/polls/5/                     詳細（質問 ID=5 の中身）
/polls/5/results/             結果
/polls/5/vote/                投票エンドポイント
```

そして次の知識が手に入ります:
- `manage.py` と `django-admin` の違い、本番運用での使い分け
- 実務でよく叩くコマンド15個
- `urlpatterns` / `path()` / `include()` / パスコンバータ
- `name` で URL に名前を付け、`reverse()` と `{% url %}` で逆引きする
- 名前空間 (`app_name`, `namespace`) で URL 名前衝突を防ぐ

---

# 第1章 manage.py と django-admin の正体

## 1-1. manage.py とは何か

`manage.py` は `django-admin startproject` で **自動生成される、プロジェクト専用のコマンドラインユーティリティ** です。中身を覗くとこうなっています（`config/` プロジェクト直下の `manage.py`）。

```python
#!/usr/bin/env python
import os
import sys

def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    # ...
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
```

ポイントは1行目の `os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")` です。これが「**このコマンドはどの settings.py を使うか**」を決めています。

## 1-2. django-admin との違い

| | `django-admin` | `python manage.py` |
|---|---|---|
| 設定ファイルの指定 | 自分で `--settings=...` か環境変数で指定する必要あり | `manage.py` 内で自動指定済み |
| 使うタイミング | プロジェクト作成時 (`startproject`) | プロジェクト作成後の **すべての操作** |
| 複数環境の切替 | 得意（`--settings=config.settings.production` など） | 一つの settings に固定 |

実務では:

- **新規プロジェクト作成時だけ** `django-admin startproject ...`
- **それ以降は基本ずっと** `python manage.py ...`
- CI/本番デプロイのスクリプトで「dev/staging/production で異なる settings を使い分けたい」ときに `django-admin --settings=...` を使うことがある

## 1-3. DJANGO_SETTINGS_MODULE の役割

Django は起動時にこの環境変数を見て **どの settings モジュールを読むか** を決めます。値は Python のドット区切りパス:

```bash
export DJANGO_SETTINGS_MODULE=config.settings
```

`manage.py` を経由するとこれが自動でセットされるので普段意識しません。意識する場面は:

1. 環境別 settings を分割したとき (`config/settings/dev.py`, `config/settings/prod.py` など)
2. Django shell や独自スクリプトを `manage.py` 経由ではなく直接 `python` で起動するとき
3. デプロイの systemd unit や Dockerfile で明示する必要があるとき

## ハンズオン① 環境を確認する

実際に `manage.py` を叩いて感触を掴みます。

```bash
# 1. ヘルプ全体を眺める（最初は圧倒されるが OK、後で戻ってくる）
uv run python manage.py help

# 2. 現プロジェクトの問題点を機械的にチェック
uv run python manage.py check

# 3. マイグレーションの適用状況を確認
uv run python manage.py showmigrations

# 4. settings.py の値を Python から確認
uv run python manage.py shell -c "from django.conf import settings; print(settings.DATABASES['default']['ENGINE']); print(settings.INSTALLED_APPS)"
```

`shell` コマンドは「**Django の設定が読み込まれた状態で Python REPL を起動する**」もので、デバッグや SQL のお試しで毎日のように使います。

---

# 第2章 実務でよく叩くコマンド15選

すべて `uv run python manage.py <command>` の形で実行できます（uv プロジェクトの場合）。

## A. プロジェクト/アプリ生成系

### 1. `startproject` — プロジェクト初期化（`django-admin` 経由）

```bash
django-admin startproject config .
```

末尾の `.` は「カレントディレクトリ直下に展開」の意味。これがないと `config/config/settings.py` のように一段ネストされる。

### 2. `startapp` — アプリ追加

```bash
uv run python manage.py startapp polls
```

`polls/` ディレクトリに `models.py`, `views.py`, `admin.py`, `migrations/`, `tests.py`, `apps.py`, `__init__.py` が作られる。Django では「機能の単位 = アプリ」と思っておけば OK。

> **アプリを作ったら必ず `INSTALLED_APPS` に追加する。** 入れ忘れると Django から見えず、テンプレートやマイグレーションも認識されない。

## B. データベース系（最頻出）

### 3. `makemigrations` — モデル変更を検出してマイグレーションファイル生成

```bash
uv run python manage.py makemigrations
uv run python manage.py makemigrations polls          # アプリ単位で生成
uv run python manage.py makemigrations --dry-run      # 何が作られるか確認だけ
```

`models.py` を変更したら **必ず** これを叩く。生成されたファイル (`polls/migrations/0001_initial.py` など) は **コミット対象**。

### 4. `migrate` — マイグレーションを DB に適用

```bash
uv run python manage.py migrate                       # 全部適用
uv run python manage.py migrate polls                 # アプリ単位
uv run python manage.py migrate polls 0003            # 特定マイグレーションまで
uv run python manage.py migrate polls zero            # アプリのテーブルを全削除（戻し）
uv run python manage.py migrate --plan                # 何が実行されるか事前確認
```

`makemigrations` が「**設計図を作る**」、`migrate` が「**設計図に従って実際に DB を変更する**」。混同しやすいので何度か手で叩いて感覚を掴むのが大事。

### 5. `showmigrations` — 適用状況を可視化

```bash
uv run python manage.py showmigrations
uv run python manage.py showmigrations --plan         # 実行順序付き
```

未適用は `[ ]`、適用済みは `[X]` で表示される。デプロイ前に「未適用が残っていないか」を確認するのに使う。

### 6. `sqlmigrate` — マイグレーションが実行する SQL を見る

```bash
uv run python manage.py sqlmigrate polls 0001
```

「このマイグレーション、何が起きるんだろう？」を **適用前に** SQL で見られる超便利コマンド。本番反映前のレビュー時に必須。

### 7. `dbshell` — DB に直接ログイン

```bash
uv run python manage.py dbshell
```

`settings.DATABASES` の設定を使って、MySQL なら `mysql`、PostgreSQL なら `psql`、SQLite なら `sqlite3` の対話シェルが起動する。`SHOW TABLES;` などを直接叩ける。

## C. 開発・運用系

### 8. `runserver` — 開発サーバ起動

```bash
uv run python manage.py runserver                     # localhost:8000
uv run python manage.py runserver 8080                # ポート変更
uv run python manage.py runserver 0.0.0.0:8000        # LAN 内の他端末から見られる
```

ファイル変更を検知して自動再読み込み。**本番環境では絶対に使わない**（Gunicorn / uWSGI などを使う）。

### 9. `shell` — Django ロード済みの Python REPL

```bash
uv run python manage.py shell

# REPL内
>>> from todo.models import Task
>>> Task.objects.all()
>>> Task.objects.create(title="買い物")
```

ORM の挙動確認、データ修正のワンショット作業、本番で `shell_plus` (django-extensions) を使った調査など、用途多数。

### 10. `createsuperuser` — Django Admin 用の管理者を作る

```bash
uv run python manage.py createsuperuser
```

対話式で username/email/password を聞かれる。作成後、`/admin/` にログインできる。

### 11. `test` — テスト実行

```bash
uv run python manage.py test                          # 全テスト
uv run python manage.py test polls                    # アプリ単位
uv run python manage.py test polls.tests.QuestionModelTests  # クラス単位
uv run python manage.py test --failfast               # 1件失敗で即停止
uv run python manage.py test --parallel auto          # CPU コア数で並列化
```

専用のテスト DB を毎回作って消すので **本物の DB は汚れない**（`migrate` だけは走る）。

### 12. `check` — 構成チェック

```bash
uv run python manage.py check
uv run python manage.py check --deploy                # 本番設定として問題ないか
```

`--deploy` オプションは `DEBUG=True` のままだったり、`SECRET_KEY` が弱かったりするのを叩いてくれる。デプロイ前 CI に組み込むのが定石。

## D. 本番デプロイ系

### 13. `collectstatic` — 静的ファイルを収集

```bash
uv run python manage.py collectstatic --noinput
```

各アプリの `static/` の中身を `STATIC_ROOT` にまとめてコピーする。Nginx などから配信するために必要。**開発環境では基本不要**。

### 14. `dumpdata` / `loaddata` — データのエクスポート/インポート

```bash
uv run python manage.py dumpdata > backup.json                      # 全データ
uv run python manage.py dumpdata polls --indent=2 > polls.json      # アプリ単位
uv run python manage.py loaddata polls.json                         # 読み込み
```

ローカルで作ったテストデータをチームで共有したり、簡易バックアップに使ったりする。

### 15. Python から呼ぶ — `call_command`

```python
from django.core.management import call_command
call_command("migrate")
call_command("dumpdata", "polls", indent=2)
```

カスタム管理コマンドや cron スクリプトの中から、他の管理コマンドを呼びたいときに使う。

---

# 第3章 URL ルーティングの仕組み

ここから本題の URL です。第1〜2章で作ってきた `polls/` を実装しながら学びます。

## 3-1. Django がリクエストを処理する流れ

ブラウザから `http://127.0.0.1:8000/polls/5/` が来たとき、Django は次の順で処理します。

1. `settings.ROOT_URLCONF` を見る → `"config.urls"` と分かる
2. `config/urls.py` の `urlpatterns` を **上から順に** 照合
3. 最初にマッチしたパターンの **ビュー関数** を呼ぶ
4. ビューが返した `HttpResponse` をレスポンスとして送る

「**順番に上から照合する**」という性質が大事です。**先に書いたほうが勝つ**ので、より具体的なパターンを上に置きます。

## 3-2. urlpatterns / path() の最小例

`config/urls.py`:

```python
from django.contrib import admin
from django.urls import path
from todo import views as todo_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", todo_views.task_list),
]
```

`path()` は最低 2 引数:

- 第1引数: **URL パターン文字列** (`"polls/<int:question_id>/"` など)
- 第2引数: **ビュー関数（または `include()` の結果）**
- 第3引数 (任意): `name="task_list"` のように URL に名前を付ける（後述）

## 3-3. パスコンバータ — URL から型付き値を抜き出す

URL の中に変数を埋め込むには `<コンバータ名:変数名>` 構文を使います。

| コンバータ | マッチするもの | 例 |
|---|---|---|
| `str` | `/` を含まない非空文字列（既定値） | `articles` |
| `int` | 0 以上の整数 | `2024` |
| `slug` | 英数字 + `-` + `_`（URL 安全な文字列） | `my-first-post` |
| `uuid` | 整形済み UUID | `075194d3-6885-...` |
| `path` | `/` を含んでもよい非空文字列 | `articles/2024/03/` |

```python
path("articles/<int:year>/", views.year_archive)
path("articles/<int:year>/<int:month>/<slug:slug>/", views.article_detail)
```

ビュー側ではキャプチャ名と同じ引数名で受け取る:

```python
def year_archive(request, year):
    # year は int 型で渡ってくる（コンバータが変換済み）
    ...
```

> **`int` で受けたら型変換不要** という点が重要。`re_path` や生の正規表現だと文字列で渡るので、自分で `int()` する必要があった。`path()` のほうが安全で読みやすい。

## ハンズオン② polls アプリにビューを実装する

現状の `polls/views.py` は空です。次のように書き換えてください。

`polls/views.py`:

```python
from django.http import HttpResponse


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


def detail(request, question_id):
    return HttpResponse(f"You're looking at question {question_id}.")


def results(request, question_id):
    return HttpResponse(f"You're looking at the results of question {question_id}.")


def vote(request, question_id):
    return HttpResponse(f"You're voting on question {question_id}.")
```

次に `polls/urls.py` を更新:

```python
from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("<int:question_id>/", views.detail, name="detail"),
    path("<int:question_id>/results/", views.results, name="results"),
    path("<int:question_id>/vote/", views.vote, name="vote"),
]
```

ここまででローカルの URL を叩いても 404 になります。プロジェクトの URLconf にまだ繋いでいないからです。次節で繋ぎます。

---

# 第4章 include() で URLconf を分割する

## 4-1. include() の意義

各アプリは **自分用の `urls.py` を持って自己完結** すべきです。プロジェクトの `urls.py` には「どの URL プレフィックスをどのアプリに任せるか」だけ書きます。

```python
# config/urls.py（プロジェクト側）
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("polls/", include("polls.urls")),  # /polls/* を polls.urls に委任
    path("", include("todo.urls")),         # / は todo に委任
]
```

`include("polls.urls")` の動きは:

1. リクエスト URL が `polls/` で始まるかチェック
2. マッチしたら `polls/` の **後ろの部分** を切り出して `polls.urls` に渡す
3. `polls/urls.py` の `urlpatterns` に対して、その残り文字列で再びマッチング

つまり `polls/urls.py` の中の `path("<int:question_id>/", ...)` は、実 URL では `/polls/<int:question_id>/` を意味します。

## ハンズオン③ プロジェクトに polls を組み込む

`config/urls.py` を見て、polls がまだ include されていなければ追加してください。

```python
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("polls/", include("polls.urls")),
    path("", include("todo.urls")),
]
```

サーバを起動して動作確認:

```bash
uv run python manage.py runserver
```

ブラウザでこれらが応答するはず:

| URL | 期待される表示 |
|---|---|
| http://127.0.0.1:8000/polls/ | `Hello, world. You're at the polls index.` |
| http://127.0.0.1:8000/polls/5/ | `You're looking at question 5.` |
| http://127.0.0.1:8000/polls/5/results/ | `You're looking at the results of question 5.` |
| http://127.0.0.1:8000/polls/5/vote/ | `You're voting on question 5.` |

`/polls/abc/` のように整数でない URL を叩くと **404 になります**。これは `int` コンバータが整数だけを受け付けるためで、嬉しい副作用としてバリデーション漏れによるバグを防げます。

## 4-2. ネストして共通プレフィックスを括り出す

3-2 の `polls/urls.py` は `<int:question_id>/` の繰り返しが目立ちます。`include()` はインラインリストも受け付けるので、こう書き直せます。

```python
from django.urls import include, path

from . import views

question_patterns = [
    path("", views.detail, name="detail"),
    path("results/", views.results, name="results"),
    path("vote/", views.vote, name="vote"),
]

urlpatterns = [
    path("", views.index, name="index"),
    path("<int:question_id>/", include(question_patterns)),
]
```

`question_id` はネスト先の各ビューにも自動で渡ります。**重複が減って読みやすくなる**ので、似たプレフィックスが3つ以上並んだら検討する価値があります。

---

# 第5章 URL に名前を付け、逆引きする

## 5-1. なぜ URL 名が必要か

URL を直書きすると、後で変えたときの修正範囲が爆発します:

```html
<!-- 悪い例: URL を直書き -->
<a href="/polls/5/results/">結果を見る</a>
```

URL の path を `/polls/5/results/` から `/polls/5/result/` に変えたら、テンプレートとビューと JS の全箇所を直す羽目になります。

代わりに **URL に名前を付け、コードからは名前で参照** します。

```python
# polls/urls.py
path("<int:question_id>/results/", views.results, name="results")
```

```html
<!-- テンプレートから -->
<a href="{% url 'results' question.id %}">結果を見る</a>
```

```python
# ビューから
from django.urls import reverse
return HttpResponseRedirect(reverse("results", args=(question.id,)))
```

これなら URL パターン側を書き換えれば全箇所が追従します。

## 5-2. reverse() と {% url %}

`reverse(name, args=(...,))` は **「名前 + 引数」から URL 文字列を生成** する関数です。`HttpResponseRedirect` や JSON レスポンスに URL を埋めるときに使います。

`{% url %}` テンプレートタグは同じことをテンプレート内でやるためのもの。

```python
# Python 側
from django.urls import reverse
reverse("detail", args=(5,))                    # → "/polls/5/"
reverse("detail", kwargs={"question_id": 5})    # 同じ結果
```

```html
<!-- テンプレート側 -->
{% url 'detail' 5 %}                            <!-- /polls/5/ -->
{% url 'detail' question_id=5 %}                <!-- 同じ -->
```

## ハンズオン④ ビューでリダイレクトを使う

`polls/views.py` の `vote` を、投票後に `results` へリダイレクトするように変えます。

```python
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse


def vote(request, question_id):
    # 本来はここで投票処理
    return HttpResponseRedirect(reverse("results", args=(question_id,)))
```

ブラウザで `http://127.0.0.1:8000/polls/5/vote/` を叩いて `/polls/5/results/` に飛べば成功。**URL 文字列を一切ハードコードしていない** のがポイント。

---

# 第6章 名前空間で衝突を防ぐ

## 6-1. 何が問題か

`todo` アプリと `polls` アプリ、両方に `name="index"` があったらどうなるでしょう？

```python
# todo/urls.py
path("", views.task_list, name="index")

# polls/urls.py
path("", views.index, name="index")
```

`reverse("index")` がどちらを返すかは **後勝ちで非決定的**。これを防ぐのが **名前空間** です。

## 6-2. アプリケーション名前空間 (`app_name`)

各アプリの `urls.py` に `app_name` を一行加えます。

```python
# polls/urls.py
from django.urls import path
from . import views

app_name = "polls"          # ← これ

urlpatterns = [
    path("", views.index, name="index"),
    path("<int:question_id>/", views.detail, name="detail"),
    path("<int:question_id>/results/", views.results, name="results"),
    path("<int:question_id>/vote/", views.vote, name="vote"),
]
```

これで参照側はこう書きます:

```python
reverse("polls:detail", args=(5,))          # /polls/5/
reverse("polls:results", args=(5,))         # /polls/5/results/
```

```html
{% url 'polls:detail' question.id %}
```

`app_name:url_name` の形式です。

## 6-3. インスタンス名前空間 — 同じアプリを複数マウントする

レアケースですが、同じアプリを別々の URL プレフィックスで複数マウントしたいときがあります（例: `author-polls/` と `publisher-polls/`）。

```python
# config/urls.py
urlpatterns = [
    path("author-polls/", include("polls.urls", namespace="author-polls")),
    path("publisher-polls/", include("polls.urls", namespace="publisher-polls")),
]
```

```python
reverse("author-polls:detail", args=(5,))     # /author-polls/5/
reverse("publisher-polls:detail", args=(5,))  # /publisher-polls/5/
```

実務でこれを使うのは「マルチテナント」「同じビューに複数のトップページを生やす」など、特殊な要件のときだけです。**普段は `app_name` だけ覚えておけば十分**。

## ハンズオン⑤ polls 全体を名前空間化する

1. `polls/urls.py` の先頭に `app_name = "polls"` を追加。
2. `polls/views.py` の `vote` 内の `reverse("results", ...)` を `reverse("polls:results", ...)` に変更。

```python
# polls/views.py
def vote(request, question_id):
    return HttpResponseRedirect(reverse("polls:results", args=(question_id,)))
```

3. ブラウザで `/polls/5/vote/` を叩いて `/polls/5/results/` に飛ぶことを確認。

> **小ワザ**: `app_name` を入れたあと `reverse("polls:results", ...)` に書き換え忘れていると、`NoReverseMatch` エラーで気づけます。テストや `check` で早期発見しやすい。

---

# 第7章 上級トピック・実務 Tips

## 7-1. パスコンバータを自作する

組み込みコンバータで足りないとき、自分で作れます。例: 4桁固定の年。

```python
# polls/converters.py
class FourDigitYearConverter:
    regex = "[0-9]{4}"

    def to_python(self, value):
        return int(value)

    def to_url(self, value):
        return f"{value:04d}"
```

```python
# polls/urls.py
from django.urls import path, register_converter
from . import converters, views

register_converter(converters.FourDigitYearConverter, "yyyy")

urlpatterns = [
    path("archive/<yyyy:year>/", views.archive),
]
```

`<int:year>` だと `/archive/2024/` も `/archive/12345/` も通ってしまうところ、`<yyyy:year>` なら `/archive/12345/` は 404 になります。

## 7-2. ビューに固定値を渡す

`path()` の第3引数に dict を渡せば、ビュー関数のキーワード引数として固定値を注入できます。

```python
# polls/urls.py
path("featured/", views.year_archive, {"year": 2024}, name="featured")
```

ビュー側:

```python
def year_archive(request, year):
    ...
```

## 7-3. エラーハンドラのカスタマイズ

```python
# config/urls.py の末尾
handler404 = "config.views.page_not_found"
handler500 = "config.views.server_error"
```

カスタム 404/500 ページを返したいときに使う。`DEBUG=False` の本番環境でだけ有効。

## 7-4. 実務でやりがちなミスと対策

| ミス | 症状 | 対策 |
|---|---|---|
| アプリを `INSTALLED_APPS` に入れ忘れる | テンプレートが見つからない / `makemigrations` が反応しない | アプリ作ったら最優先で追記 |
| `path("polls", ...)` のように末尾スラッシュなし | `/polls/` でアクセスすると無限リダイレクトや 404 | Django は **末尾スラッシュ派**。`"polls/"` に統一 |
| URL を直書き | URL 変更で全コードを grep する羽目に | `name=` + `{% url %}` / `reverse()` で逆引き |
| 名前空間なし | 大規模化したとき `name` 衝突 | アプリ作ったら最初に `app_name` を入れる |
| `path()` の順序ミス | 一般パターンが具体的パターンを食う | より具体的なものを上に書く |

## 7-5. デバッグの定番技

URL ルーティングの不調は次の順で切り分けると速い:

```bash
# 1. 構成エラーがないか
uv run python manage.py check

# 2. 認識されている URL を一覧（django-extensions が要る）
uv run python manage.py show_urls

# 3. shell で reverse を試す
uv run python manage.py shell -c "from django.urls import reverse; print(reverse('polls:detail', args=(1,)))"

# 4. 実際にリクエストして 200/404 を見る
curl -I http://127.0.0.1:8000/polls/1/
```

`show_urls` は標準コマンドではなく `django-extensions` パッケージ提供。実務では入れる価値あり (`uv add django-extensions`)。

---

# 付録: チートシート

## URL コンバータ早見表

```
<str:slug>      "/" を含まない文字列
<int:id>        正の整数
<slug:s>        [a-z0-9_-]+
<uuid:u>        UUID
<path:p>        "/" を含む文字列（残り全部）
```

## URL 逆引き早見表

```python
# Python
reverse("polls:detail", args=(5,))
reverse("polls:detail", kwargs={"question_id": 5})

# テンプレート
{% url 'polls:detail' 5 %}
{% url 'polls:detail' question_id=5 %}
```

## 主要コマンド早見表

```bash
# プロジェクト
django-admin startproject NAME .
uv run python manage.py startapp NAME

# DB
uv run python manage.py makemigrations
uv run python manage.py migrate
uv run python manage.py showmigrations
uv run python manage.py sqlmigrate APP NUMBER
uv run python manage.py dbshell

# 開発
uv run python manage.py runserver
uv run python manage.py shell
uv run python manage.py createsuperuser

# 検査・テスト
uv run python manage.py check
uv run python manage.py check --deploy
uv run python manage.py test

# データ
uv run python manage.py dumpdata APP > backup.json
uv run python manage.py loaddata backup.json
```

---

# まとめ

ここまで読み終えて、ハンズオン①〜⑤を全部こなしたなら次のことができるはずです。

- `manage.py` を「**設定済みの django-admin**」として使える
- `makemigrations` と `migrate` の役割の違いを説明できる
- URL リクエストが `urlpatterns` を上から照合される流れを追える
- `path()` のパスコンバータで型付きの引数をビューに渡せる
- `include()` で URLconf を分割できる
- `name=` と `app_name=` を使って URL を参照する側のハードコードをゼロにできる

次に学ぶべきは:

- **テンプレート** (`render`) と **モデル** (`models.py`) の連携
- **Django Admin** のカスタマイズ
- **クラスベースビュー** (`ListView`, `DetailView`)
- **フォーム** と CSRF

これらは別ドキュメントで扱います。
