# Django プロジェクト作成と開発サーバ完全入門

> **このドキュメントの読み方**
> 上から順に読み、コードブロックを **自分の手で** 実行しながら進めてください。手元の `roadmap-sh-django` リポジトリは既に動いている状態ですが、本ドキュメントでは **「もし今からゼロで作るならどう作るか」** を再現したうえで、いま動いているプロジェクトの構造が **なぜそうなっているか** を理解できる構成にしてあります。ハンズオンでは現プロジェクトを壊さず、別のディレクトリにお試し用の「scratch」プロジェクトを作って学びます。
>
> **前提**:
> - Python 3.14 と `uv` がインストール済み
> - 本リポジトリ `roadmap-sh-django` が動く状態
> - `docs/01〜03` の内容（manage.py、URL、モデル、テンプレート、static/media）に概ね目を通している

---

## このドキュメントで分かること

完走後に身につく知識：
- `django-admin startproject` が **何を作って、どこに何が置かれるか**
- `manage.py` の中身と、**なぜ「`python manage.py` ではなく `uv run python manage.py`」になるのか**
- `runserver` と `runserver_plus` の違い、auto-reload の仕組み・限界
- ポート指定、IP バインド、`ALLOWED_HOSTS`、`DEBUG` の関係
- **なぜ開発サーバを本番で使ってはいけないのか**（5つの理由）
- `startapp` で新しいアプリを増やすときの手順（`INSTALLED_APPS` 登録、ルート URL conf への include まで）
- 本番で使う WSGI/ASGI サーバ（`gunicorn` / `uvicorn` / `daphne`）の選び方
- 起動時に詰まる典型エラー（ポート競合、`ALLOWED_HOSTS`、404、`SECRET_KEY` 未設定 など）

---

# 第1章 Django プロジェクトを「作る」とは

## 1-1. プロジェクト ≠ アプリ

Django には **プロジェクト (project)** と **アプリ (app)** という2つの単位があります：

| 単位 | 説明 | 例 |
|---|---|---|
| プロジェクト | **Web サイト1つ全体の設定** をまとめた箱 | このリポジトリの `config/` |
| アプリ | プロジェクト内の **機能単位**。複数のプロジェクトで使い回せる | `polls/`、`todo/` |

イメージは：

```
プロジェクト「アンケートサイト」
├── 設定 (DB 接続、ミドルウェア、INSTALLED_APPS, ルート URL conf, ...)
├── アプリ: polls
└── アプリ: todo
```

プロジェクトは「サイト全体の設定束」、アプリは「機能の塊」。同じ `polls` アプリを別のプロジェクトに持っていって再利用することもできます。

## 1-2. `django-admin` と `manage.py` の関係

Django には2つの似たコマンドがあります：

| コマンド | いつ使う |
|---|---|
| `django-admin` | プロジェクトを **まだ作っていない状態** で使う。代表は `startproject` |
| `python manage.py` | プロジェクトを **作った後**、その中で使う |

`django-admin` は `pip install django` で入る実行ファイル。`manage.py` は `startproject` の時に生成され、そのプロジェクト用にカスタマイズされた django-admin の薄いラッパーです（詳しくは第3章）。

## 1-3. `startproject` の動き

新規プロジェクトはこれ1行で作れます：

```bash
django-admin startproject mysite
```

実行後のディレクトリ構造：

```
mysite/                  ← 外側の「プロジェクトのルート」(任意の名前)
├── manage.py
└── mysite/              ← 内側の「プロジェクトモジュール」(startproject の引数)
    ├── __init__.py
    ├── settings.py
    ├── urls.py
    ├── asgi.py
    └── wsgi.py
```

**重要**: `mysite/mysite/` と同じ名前が2回出てきます。**外側はファイルシステム上のフォルダ**、**内側は Python パッケージ**です。混乱しやすいので明確に区別してください。

外側の `mysite/` を別名にしたい場合は引数を2つ渡します：

```bash
django-admin startproject mysite myproject
# myproject/         ← 外側はこの名前に
# └── mysite/        ← 内側は startproject の第1引数のまま
#     └── ...
```

## 1-4. なぜこのリポジトリは `config/` という名前なのか

このリポジトリで `django-admin startproject` 相当をやったときに、内側の Python パッケージを `config` という名前にしたからです。標準だと「サイト名 = Python パッケージ名」となり：

```python
# settings.py 内で
WSGI_APPLICATION = "mysite.wsgi.application"
ROOT_URLCONF = "mysite.urls"
```

のように **サイト名がプロジェクトの内部実装に染み出して** しまいます。あとから「サイト名を変えたい」「プロジェクト名を別にしたい」となったときに settings.py をはじめあちこち直さないといけないので、コミュニティでは：

- `config/` — 設定の集まりだから、と命名する派（このリポジトリも採用）
- `core/` — 中核モジュールだから、と命名する派
- `project/` — 機能ではなくプロジェクト由来だと示す派

のように **役割を表す中立名** に変えることが多いです。Django の有名なプロジェクトテンプレート [cookiecutter-django](https://github.com/cookiecutter/cookiecutter-django) も `config/` を採用しています。

## ハンズオン 1: scratch プロジェクトを作ってみる

既存リポジトリを壊さないように、**ホームディレクトリの下** に別のお試し用プロジェクトを作ります。

### 1. お試し用ディレクトリを作る

```bash
mkdir -p ~/django-scratch
cd ~/django-scratch
```

### 2. `uv` でプロジェクト雛形を作る

```bash
uv init --bare
uv add 'django>=6.0'
```

`uv init --bare` は最低限の `pyproject.toml` だけ作るオプションです。`uv add django` で Django をインストールしつつ `pyproject.toml` の依存関係に追加し、`.venv/` を自動で作ってくれます。

### 3. `django-admin startproject` を実行

```bash
uv run django-admin startproject mysite .
```

末尾の `.`（カレントディレクトリ）に注目。これを付けると `mysite/mysite/` の二重ネストではなく、`./manage.py` + `./mysite/` という1階層構造になります（このリポジトリの構造に近い形）。

### 4. ツリーを確認

```bash
ls -la
```

`manage.py` と `mysite/` ディレクトリ（中に `settings.py` などが入っている）ができていれば成功です。

```
~/django-scratch/
├── .python-version
├── .venv/
├── pyproject.toml
├── uv.lock
├── manage.py            ← startproject が生成
└── mysite/              ← startproject が生成
    ├── __init__.py
    ├── settings.py
    ├── urls.py
    ├── asgi.py
    └── wsgi.py
```

### 5. このまま動かしてみる

```bash
uv run python manage.py runserver
```

ブラウザで http://127.0.0.1:8000 を開くと「The install worked successfully! Congratulations!」のロケットアイコンのページが出ます。`Ctrl-C` で停止しておきます。

> **注意**: DB マイグレーション未適用の警告が出ますが、最初の確認では無視して OK。`runserver` が起動さえすればこの章のゴールは達成です。

---

# 第2章 生成されたファイルツリーを読み解く

## 2-1. `manage.py` — プロジェクト操作の入り口

```python
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
```

短いですが大事な仕事を3つしています：

1. **`DJANGO_SETTINGS_MODULE` を環境変数にセット** → Django がどの settings.py を読むか決まる
2. **`django.core.management` を import** → 失敗したら親切なエラーを出す
3. **`execute_from_command_line(sys.argv)`** → 受け取った引数に応じてサブコマンドを実行

つまり「`python manage.py runserver`」というコマンドは：
- 環境変数 `DJANGO_SETTINGS_MODULE=mysite.settings` をセットしてから
- Django の `runserver` コマンドを実行する

ということを意味します。

## 2-2. `settings.py` — プロジェクトの全設定

代表的なキー：

| 設定 | 役割 |
|---|---|
| `SECRET_KEY` | Cookie の署名、CSRF トークン、パスワードハッシュなどに使われる秘密鍵。**漏らすな** |
| `DEBUG` | `True` だとエラー画面に詳細・スタックトレースが出る。**本番では必ず `False`** |
| `ALLOWED_HOSTS` | 受け付ける Host ヘッダの値の許可リスト。`DEBUG=False` のとき必須 |
| `INSTALLED_APPS` | 有効化するアプリの Python パス（ドット区切り） |
| `MIDDLEWARE` | リクエスト/レスポンスを横断する処理の連鎖 |
| `ROOT_URLCONF` | ルート URL conf モジュールのパス（このリポジトリだと `"config.urls"`） |
| `TEMPLATES` | テンプレートエンジン設定（→ docs/03 第1章 1-3） |
| `DATABASES` | DB 接続情報 |
| `WSGI_APPLICATION` | デプロイ時の WSGI エントリーポイント |
| `LANGUAGE_CODE` / `TIME_ZONE` / `USE_TZ` | 国際化 |
| `STATIC_URL` / `MEDIA_URL` 等 | 静的/メディアファイル（→ docs/03 第4〜6章） |

## 2-3. `urls.py` — ルート URL conf

`startproject` 直後の `mysite/urls.py`：

```python
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
]
```

`/admin/` だけ最初から登録されています。アプリを足したら `include()` でここに繋いでいきます（第7章で実演）。

## 2-4. `wsgi.py` / `asgi.py` — 本番デプロイの入り口

```python
# mysite/wsgi.py の中身（大事なところだけ）
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
application = get_wsgi_application()
```

| ファイル | 用途 |
|---|---|
| `wsgi.py` | **同期型** の本番サーバ（gunicorn など）が読み込むエントリ |
| `asgi.py` | **非同期対応** の本番サーバ（uvicorn / daphne / hypercorn）が読み込むエントリ |

両方とも `application` という名前のグローバル変数を公開しています。本番では：

```bash
gunicorn mysite.wsgi:application       # WSGI
uvicorn mysite.asgi:application        # ASGI
```

のように指定して起動します。**`runserver` ではない**ことに注意。

## 2-5. `__init__.py` — Python パッケージのしるし

中身は空ですが、これが **`mysite/` を Python パッケージとして扱わせる** ために必要です。これがないと `from mysite import settings` のような import が動かなくなります。

---

# 第3章 `manage.py` のコマンド一覧

`python manage.py help` を叩くと全コマンドが一覧で出てきます。代表的なものを役割別に：

## 3-1. 開発サーバ系

```bash
python manage.py runserver           # 開発サーバ起動（標準）
python manage.py runserver 0:8080    # IP / ポート指定
python manage.py runserver_plus      # django-extensions が提供する強化版（→ 第5章）
```

## 3-2. データベース系

```bash
python manage.py makemigrations      # モデル変更からマイグレーションファイルを生成
python manage.py migrate             # マイグレーションを適用
python manage.py showmigrations      # 適用状態の確認
python manage.py sqlmigrate APP_NAME 0001    # マイグレーションを SQL に変換して表示
python manage.py dbshell             # DB のシェル（mysql / psql など）に直接接続
```

## 3-3. アプリ・ユーザー系

```bash
python manage.py startapp APP_NAME      # 新しいアプリの雛形を生成
python manage.py createsuperuser        # admin にログインできる管理者ユーザーを作成
python manage.py changepassword USER    # パスワード変更
```

## 3-4. 対話・調査系

```bash
python manage.py shell               # Python シェル + Django セットアップ済み
python manage.py shell_plus          # django-extensions の強化版（モデル自動 import）
python manage.py check               # プロジェクトの設定エラー検出
python manage.py diffsettings        # デフォルトと違う設定だけ表示
python manage.py show_urls           # 登録済みの全 URL を一覧（django-extensions）
```

## 3-5. テスト・静的ファイル系

```bash
python manage.py test                # テスト実行
python manage.py collectstatic       # 全アプリの static を STATIC_ROOT に集める
python manage.py findstatic FILE     # static ファイルがどこにあるか調査
```

## 3-6. uv 環境での流儀

このリポジトリは `uv` 管理なので、上の全コマンドの先頭に **`uv run`** を付けます：

```bash
uv run python manage.py runserver
uv run python manage.py migrate
```

`uv run` は「**プロジェクトの仮想環境を有効化した状態で** 後続のコマンドを実行する」シェルラッパーです。`source .venv/bin/activate` を毎回打たなくて済むのが利点。

「`uv run` を毎回打つの長いので alias 切りたい」というのは普通の感覚で、`.zshrc` などに：

```bash
alias mp='uv run python manage.py'
```

としておくと `mp runserver` だけで起動できます。

---

# 第4章 開発サーバ `runserver` を理解する

## 4-1. 基本

```bash
uv run python manage.py runserver
```

これで `http://127.0.0.1:8000/` で待ち受けが始まります。

```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
Django version 6.0.4, using settings 'config.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

`Ctrl-C` で止まります。

## 4-2. ポート指定

```bash
uv run python manage.py runserver 8001     # ポートだけ指定
uv run python manage.py runserver 0:8001   # 全 IP からの接続を受ける + ポート
```

| 指定 | 意味 |
|---|---|
| `8001` | `127.0.0.1:8001`（自分のマシンからだけ） |
| `0:8001` または `0.0.0.0:8001` | 全 IP で待ち受け（LAN 内の別端末からも見える） |
| `192.168.1.10:8001` | 指定 IP のみで待ち受け |
| `[::1]:8001` | IPv6 のローカルホスト |

「スマホで実機確認したい」というときは `0:8000` で起動して、PC の LAN IP（`ifconfig` などで確認）にスマホからアクセス、というパターンになります。

## 4-3. Auto-reload の仕組み

`runserver` は **ファイル変更を監視し、Python コードが変わったら自動で再起動** します。実装は2系統：

| Reloader | 仕組み | 速度 |
|---|---|---|
| `StatReloader`（デフォルト） | 全ファイルの `stat()` をループで叩く | 遅め（数百ms） |
| `WatchmanReloader` | Facebook の watchman を使った OS イベント駆動 | 速い |

watchman を入れている環境（`brew install watchman`）では自動的に切り替わります。`Watching for file changes with WatchmanReloader` と起動ログに出ていればそちら。

### 拾うもの・拾わないもの

| 変更 | 拾う？ |
|---|---|
| Python ファイル (`.py`) の変更 | ✅ |
| 新規 Python ファイルの追加 | ✅ |
| `settings.py` の変更 | ✅（再起動される） |
| Python ファイルの **構文エラー** | ⚠️ プロセスは生き残るが、修正するまでビューが動かない |
| テンプレート (`.html`) の変更 | ❌ **拾わない**（次のリクエストで再読み込み） |
| 静的ファイル (`.css`, `.js`) の変更 | ❌（ブラウザのキャッシュをハードリロードすればよい） |
| マイグレーションの適用 | ❌（手動で `migrate` 後に再起動が必要） |

「テンプレート変えたのに見た目が変わらない」と思ったら、それは reload 対象外だからではなく **キャッシュ** か **ブラウザの強制リロード忘れ** が多いです。テンプレート自体は次のリクエストで再読み込みされます。

## 4-4. `DEBUG=True` のとき開発サーバが追加でやってくれること

1. **詳細なエラーページ**: 500 エラーが出るとスタックトレース、SQL クエリ、設定値などを HTML で表示
2. **静的ファイルの自動配信**: `staticfiles` アプリが `STATIC_URL` 以下を動的に解決
3. **メディアファイルの自動配信**: ただし `urls.py` で `static()` を仕込んだ場合のみ（→ docs/03 6-3）
4. **テンプレートのキャッシュ無効化**: 編集即反映

これら全部 **`DEBUG=False` ではオフ** になります。本番では Django ではなく Nginx などに任せるのが原則。

## 4-5. `ALLOWED_HOSTS` の落とし穴

`DEBUG=True` のときは `ALLOWED_HOSTS=[]` でも `127.0.0.1` と `localhost` は自動で許可されます。が、`DEBUG=False` に切り替えた瞬間に **明示しないと一切のリクエストが弾かれます**：

```
DisallowedHost at /
Invalid HTTP_HOST header: 'example.com'.
You may need to add 'example.com' to ALLOWED_HOSTS.
```

開発で `DEBUG=False` の挙動を確認したい場合は：

```python
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
```

を入れておきます。本番では実際のドメインを入れる：

```python
ALLOWED_HOSTS = ["example.com", "www.example.com"]
```

`["*"]` は「任意のホスト名から来た任意のリクエストを受ける」という意味で、**Host ヘッダー詐称攻撃** を防げなくなるので本番ではダメです（開発用テスト目的なら可）。

## ハンズオン 2: runserver のオプションを試す

scratch プロジェクトに戻って、いろいろ試してみましょう。

### 1. ポートを変えて起動

```bash
cd ~/django-scratch
uv run python manage.py runserver 8888
```

ブラウザで http://127.0.0.1:8888 にアクセス。8000 とは別ポートで動いていることを確認。

### 2. LAN に公開して別端末から見る

```bash
uv run python manage.py runserver 0:8000
```

ターミナルに `Starting development server at http://0.0.0.0:8000/` と出る。`ifconfig | grep "inet " | grep -v 127.0.0.1` で自分のローカル IP を調べて、同じ LAN にいるスマホやタブレットからその IP の :8000 にアクセス。

> **macOS のファイアウォール**: アクセスできない場合、「システム設定 → ネットワーク → ファイアウォール」で許可するか、一時的にオフにしてください。

### 3. 構文エラーで止まる挙動を見る

`mysite/urls.py` をエディタで開いて、わざと壊します：

```python
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),   # ← この行の "admin/" の " を消す
```

保存すると、`runserver` のターミナルに大きなトレースバックが出るはず：

```
SyntaxError: ... (urls.py, line N)
```

`runserver` プロセス自体は生きていて、エラーを直して保存すれば自動で復帰します。**プロセスごと落とさず、Python の構文エラーで止まる** だけの設計は親切。

直したら元に戻しておきます。

### 4. テスト中は `Ctrl-C` で停止

scratch プロジェクトでの確認はここまで。`Ctrl-C` で停止しておきます。

---

# 第5章 `runserver_plus` (django-extensions)

このリポジトリの開発用コマンドは `runserver` ではなく `runserver_plus` を使っています：

```bash
uv run python manage.py runserver_plus
```

`runserver` との違いをまとめます。

## 5-1. Werkzeug デバッガ

500 エラーが起きたとき、エラー画面上で **インタラクティブな Python シェル** が開けます。スタックの各フレームでローカル変数を確認したり、その場で式を評価できる。これだけでも `runserver_plus` を使う価値があります。

> **注意**: Werkzeug デバッガは **任意のコードを実行可能** なので、`0:8000` で LAN に開けっぱなしにしないこと。デバッガ起動時のターミナルに PIN コードが出るので、それを入力してロック解除する仕組みになっています。

## 5-2. SSL/HTTPS

```bash
uv run python manage.py runserver_plus --cert-file /tmp/cert.crt
```

自己署名証明書を自動生成して HTTPS で起動できます。OAuth コールバック URL を試すときなど「localhost でも HTTPS じゃないと困る」ケースで便利。

## 5-3. `--print-sql` 系（このプロジェクトでは使わない）

これは過去のドキュメントで触れたとおり、debug_toolbar と二重で動くと出力が混乱します。代わりに `config/settings.py` の `LOGGING` で `django.db.backends` を DEBUG レベルで仕込んであります（このリポジトリの構成）。

## 5-4. なぜ runserver_plus を選ぶか

| 機能 | `runserver` | `runserver_plus` |
|---|---|---|
| Auto-reload | ✅ | ✅（Werkzeug 経由） |
| Werkzeug 対話デバッガ | ❌ | ✅ |
| HTTPS 自己署名 | ❌ | ✅ |
| 拡張オプション (`--print-sql` 等) | ❌ | ✅ |
| 依存 | Django のみ | `django-extensions` + `werkzeug` |

`django-extensions` を入れている場合は `runserver_plus` に揃える、というのが定番です。

---

# 第6章 開発サーバを本番で使ってはいけない5つの理由

`runserver`/`runserver_plus` を起動すると毎回こう警告されます：

```
WARNING: This is a development server. Do not use it in a production deployment.
Use a production WSGI server instead.
```

理由はちゃんと5つあります：

## 6-1. シングルプロセス・シングルスレッド（標準）

`runserver` は **同時に1つのリクエストしか処理しない** のがデフォルト。秒間100リクエスト程度でもキューが詰まって落ちます。`--nothreading` を外しても、それでもプロセスが1つなので CPU マルチコアを活かせません。

本番では `gunicorn -w 4` のように **複数 worker プロセス** を立てて、コア数の数倍のリクエストを並列処理します。

## 6-2. クラッシュ復旧機能なし

ワーカープロセスが落ちた / メモリリークで肥大化した、というときに本番サーバ（gunicorn など）は自動で worker を入れ替えます。`runserver` は落ちたらそこで終わり。

## 6-3. 静的ファイル配信が非効率

`DEBUG=True` のとき `runserver` は static/media ファイルも Python で配信しますが、これは **ファイル送出を Nginx などのネイティブ実装に任せたほうが圧倒的に速い** ものを Python でやっているだけ。本番では Nginx に `location /static/` を書くか、WhiteNoise を仕込みます（→ docs/03 第5章）。

## 6-4. セキュリティ機構が薄い

`runserver` は HTTPS 終端、レート制限、HTTP/2、コネクションタイムアウト管理など、Web サーバが当然備えるべき機能を **持っていません**。

## 6-5. 設計思想が「開発体験優先」

そもそも `runserver` のコードを読むと、**開発体験のためのショートカット** が多く入っています（auto-reload、`DEBUG` 時の自動 static 配信、Werkzeug デバッガ連携）。これらは本番には不要、むしろ有害です。

## 6-6. じゃあ本番では何を使うか

| サーバ | 種類 | 特徴 | 起動例 |
|---|---|---|---|
| **gunicorn** | WSGI | 一番枯れた定番。プロセス管理が素直 | `gunicorn config.wsgi:application -w 4 -b 0.0.0.0:8000` |
| **uvicorn** | ASGI | 非同期対応。Django 5+ の `async def` ビューを活かしたいなら | `uvicorn config.asgi:application --workers 4 --host 0.0.0.0` |
| **daphne** | ASGI | Django Channels（WebSocket）と組み合わせるなら | `daphne -b 0.0.0.0 -p 8000 config.asgi:application` |
| **hypercorn** | ASGI | uvicorn の代替候補 | `hypercorn config.asgi:application` |

そして **どれを使うにせよ前段に Nginx を置く** のが王道。`Nginx → gunicorn (Django)` という構成。

---

# 第7章 `startapp` で新しいアプリを足す

## 7-1. 流れの全体像

新しいアプリを追加するときの作業は **5ステップ**：

1. `python manage.py startapp <app名>` で雛形を生成
2. `INSTALLED_APPS` に追加
3. アプリの `views.py` にビューを書く
4. アプリの `urls.py` に URL パターンを書く（新規作成）
5. プロジェクトのルート `urls.py` に `include()` で繋ぐ

これは `polls/` や `todo/` を作ったときと同じ流れです。新しいアプリを足すときに毎回出てくる定型仕事。

## 7-2. `startapp` が生成するファイル

```bash
uv run python manage.py startapp greetings
```

```
greetings/
├── __init__.py
├── admin.py            # admin への登録（モデルを作ったら使う）
├── apps.py             # アプリの設定クラス
├── migrations/
│   └── __init__.py     # マイグレーションは「ある」とみなされる
├── models.py           # データモデル定義
├── tests.py            # テストコード
└── views.py            # リクエスト処理関数
```

注意: **`urls.py` は startapp では作られない** ので自分で作ります。

## 7-3. `INSTALLED_APPS` への登録: 2通り

```python
# settings.py
INSTALLED_APPS = [
    ...,
    "greetings",                              # 短い書き方
    # "greetings.apps.GreetingsConfig",       # 長い書き方（フル明示）
]
```

両方とも動きますが意味が少し違います：

| 書き方 | 動作 |
|---|---|
| `"greetings"` | Django が `greetings.apps` を自動で探し、`AppConfig` のサブクラスを1つ見つけて使う |
| `"greetings.apps.GreetingsConfig"` | 明示的にこのクラスを使うよう指示 |

**1つのアプリに `AppConfig` サブクラスが2つ以上ある** ような特殊ケースでは後者でないと駄目ですが、99% のケースで前者でOK。このリポジトリも `"polls"` `"todo"` の短い書き方で統一されています。

## 7-4. `apps.py` の中身

`startapp` で生成される `greetings/apps.py`：

```python
from django.apps import AppConfig


class GreetingsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "greetings"
```

| 属性 | 意味 |
|---|---|
| `name` | アプリの Python パッケージ名（変えない） |
| `default_auto_field` | モデルで `id` を明示しなかったときの自動主キー型 |
| `verbose_name` | admin での表示名（オプション） |
| `ready()` | 起動時のフック（シグナル登録などに使う、オプション） |

通常は触りませんが、シグナルを使うアプリでは `ready()` に登録処理を書く流儀があります。

## ハンズオン 3: scratch プロジェクトに `greetings` アプリを足す

第1章で作った `~/django-scratch` でやります。**メインのリポジトリは触らないでください**。

### 1. アプリ生成

```bash
cd ~/django-scratch
uv run python manage.py startapp greetings
```

### 2. `INSTALLED_APPS` に追加

`mysite/settings.py` を編集：

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "greetings",        # ← 追加
]
```

### 3. ビューを書く

`greetings/views.py`：

```python
from django.http import HttpResponse


def hello(request):
    return HttpResponse("こんにちは、Django!")


def hello_name(request, name):
    return HttpResponse(f"こんにちは、{name} さん!")
```

`hello_name` の方は URL から引数を取る練習を兼ねています。

### 4. アプリの URL conf を作る

`greetings/urls.py` を **新規作成**：

```python
from django.urls import path
from . import views

app_name = "greetings"

urlpatterns = [
    path("", views.hello, name="hello"),
    path("<str:name>/", views.hello_name, name="hello_name"),
]
```

`app_name = "greetings"` を入れると `{% url 'greetings:hello' %}` のように **名前空間付きで** 逆引きできます（→ docs/01 で扱った概念）。

### 5. ルート URL conf に include

`mysite/urls.py`：

```python
from django.contrib import admin
from django.urls import include, path     # ← include を import

urlpatterns = [
    path("admin/", admin.site.urls),
    path("greetings/", include("greetings.urls")),   # ← 追加
]
```

### 6. 動作確認

```bash
uv run python manage.py runserver
```

ブラウザで：

| URL | 期待される表示 |
|---|---|
| http://127.0.0.1:8000/greetings/ | こんにちは、Django! |
| http://127.0.0.1:8000/greetings/Junya/ | こんにちは、Junya さん! |
| http://127.0.0.1:8000/greetings/世界/ | こんにちは、世界 さん! |

`<str:name>/` の **path converter** がスラッシュ以外の任意の文字を `name` 変数に拾います。日本語も OK。

### 7. 後片付け

scratch はあくまで練習用なので、確認後は丸ごと消してかまいません：

```bash
cd ~
rm -rf ~/django-scratch
```

---

# 第8章 よくあるエラー集

## 8-1. `Error: That port is already in use.`

別のプロセスがすでに 8000 番ポートを使っています。原因は概ね：
- 別のターミナルで `runserver` を起動しっぱなしにしている
- 過去の起動がきれいに終了せずプロセスだけ残っている

**対処**：

```bash
# 8000 番を使っているプロセスを探す
lsof -i :8000

# 落とす
lsof -ti :8000 | xargs kill -9
```

または別のポートで起動：

```bash
uv run python manage.py runserver 8001
```

## 8-2. `DisallowedHost`

```
DisallowedHost at /
Invalid HTTP_HOST header: 'example.com'. You may need to add 'example.com' to ALLOWED_HOSTS.
```

`DEBUG=False` で `ALLOWED_HOSTS` 未設定。`settings.py` で許可するホスト名を明示します：

```python
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "example.com"]
```

## 8-3. `Page not found (404)`

```
Page not found (404)
Request Method: GET
Request URL: http://localhost:8000/greetings/

Using the URLconf defined in mysite.urls, Django tried these URL patterns, in this order:
  1. admin/
  2. polls/
```

`mysite.urls` が見ている URLconf が、`greetings/` を含んでいない。考えられる原因：
- ルート `urls.py` に `path("greetings/", include("greetings.urls"))` を書き忘れた
- スペルが違う（`greetings` と `greeting` など）
- サーバが再起動されていない（保存後に runserver が反応していない）

`DEBUG=True` だと **404 ページが「試した URL パターン」を全部見せてくれる** ので、それを読むのが最短。

## 8-4. `No module named 'polls'`

`INSTALLED_APPS` に書いた文字列が間違っているか、Python パスから見えていない。

- スペルチェック
- `polls/__init__.py` が存在するか
- カレントディレクトリが `manage.py` のある場所か

## 8-5. `ImproperlyConfigured: The SECRET_KEY setting must not be empty`

`settings.py` で：

```python
SECRET_KEY = os.environ["SECRET_KEY"]
```

のように環境変数から読み込んでいる場合、その環境変数が未設定だとここで死にます。

このリポジトリでは `.env` ファイルを `python-dotenv` で読んでいるので、`.env` に：

```
SECRET_KEY=django-insecure-xxxx
```

があるか確認。`.env.example` が雛形としてあります。

## 8-6. `OperationalError: (1045, "Access denied for user '...'@'localhost'")`

MySQL の認証エラー。`.env` の `DB_USER` / `DB_PASSWORD` が DB 側のユーザーと一致しているか、`DB_HOST` `DB_PORT` が正しいか確認。Homebrew の MySQL の場合、初期パスワードがないことがあります（`mysql -u root` で入れるか試す）。

## 8-7. `RuntimeError: Model class X doesn't declare an explicit app_label`

モデルファイルを `INSTALLED_APPS` に登録していないアプリ内に書いたか、アプリ名のスペルがズレている。`apps.py` の `name` と `INSTALLED_APPS` の文字列が一致しているか確認。

## 8-8. テンプレートが反映されない

`runserver` のテンプレート再読み込みは「次のリクエスト時」なので、ブラウザを **強制リロード**（Cmd+Shift+R / Ctrl+Shift+R）して効くことが多い。それでもダメなら：
- テンプレートのパスが間違っている（`{% extends "polls/base.html" %}` のパスが解決できていない）
- ファイル名の末尾にスペースが入っている（過去にあったやつ）
- アプリの `templates/` ディレクトリが `templates/<app名>/` の2階層になっていない

## 8-9. `csrf_token` 関連

```
Forbidden (CSRF cookie not set.)
```

POST フォームで `{% csrf_token %}` を入れ忘れているとこれが出ます。ファイルアップロードフォームでは `enctype="multipart/form-data"` も忘れずに（→ docs/03 第6章）。

---

# 第9章 WSGI と ASGI、どちらを使う？

## 9-1. それぞれの特徴

| | WSGI | ASGI |
|---|---|---|
| プロトコル | リクエスト→レスポンスの **同期 1往復** | 同期 + **非同期** + WebSocket / 長寿命接続 |
| 出た時期 | 2003 (PEP 333) | 2018 |
| Django 対応 | 全バージョン | 3.0+ |
| `async def view(request)` | ❌（動くが結局同期化される） | ✅ ネイティブで効く |
| 代表サーバ | gunicorn, uWSGI | uvicorn, daphne, hypercorn |
| WebSocket | 不可（Django Channels で別ルート） | 可（Channels も ASGI 経由） |

## 9-2. どっちを使うか

| 状況 | 推奨 |
|---|---|
| 普通の REST API / CRUD | WSGI (`gunicorn`) で十分。これが一番枯れている |
| `async def` ビューを書きたい | ASGI (`uvicorn`) |
| WebSocket・SSE を使う | ASGI（必須） |
| 既存サイトを「とりあえず移行」 | WSGI から始めて、必要になったら ASGI へ |

**迷ったら WSGI**。Django で非同期が真価を発揮するのは「外部 API を並列に叩く I/O 待ちが多いビュー」など限られた用途で、普通の DB 中心の Web サイトなら同期で十分です。

## 9-3. 設定の違い

`config/wsgi.py` と `config/asgi.py` は中身が違うだけで、両方とも `startproject` で自動生成されています。本番デプロイで参照するエントリの種類が違うだけ：

```python
# config/wsgi.py
application = get_wsgi_application()

# config/asgi.py
application = get_asgi_application()
```

`runserver` は内部的に WSGI を使っています。`uvicorn config.asgi:application` を直接動かしたいときは ASGI 側を指定。

---

# 付録 A: uv での「Django プロジェクト立ち上げ」テンプレ

新規プロジェクトを uv で立ち上げる時の最小コマンド集：

```bash
# 1. プロジェクトディレクトリ
mkdir myproject && cd myproject

# 2. uv 初期化
uv init --bare

# 3. Django 追加
uv add 'django>=6.0'

# 4. 共通依存（このリポジトリで使ってるやつ）
uv add 'mysqlclient' 'python-dotenv'
uv add --dev 'django-debug-toolbar' 'django-extensions' 'werkzeug' 'pygments'

# 5. Django プロジェクト生成（カレント直下に展開）
uv run django-admin startproject config .

# 6. .env を用意
echo "SECRET_KEY=django-insecure-$(uv run python -c 'import secrets; print(secrets.token_urlsafe(50))')" > .env

# 7. .gitignore
cat >> .gitignore <<'EOF'
.venv/
__pycache__/
*.pyc
.env
staticfiles/
media/
db.sqlite3
EOF

# 8. 起動
uv run python manage.py migrate
uv run python manage.py runserver
```

`startproject config .` の **末尾の `.`** がポイント。これがないと `config/config/...` の二重ネストになります。

---

# 付録 B: ファイル構造の対比

`django-admin startproject mysite` 直後 vs このリポジトリ：

```
─── startproject 直後 (canonical) ───────
mysite/
├── manage.py
└── mysite/                  ← サイト名と同じ Python パッケージ
    ├── __init__.py
    ├── settings.py
    ├── urls.py
    ├── asgi.py
    └── wsgi.py


─── このリポジトリ ──────────────────────
roadmap-sh-django/
├── manage.py
├── config/                  ← サイト名と切り離した「設定の集まり」
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   ├── wsgi.py
│   └── log_formatters.py    ← 追加で置いたモジュール
├── polls/                   ← アプリ
├── todo/                    ← アプリ
├── docs/                    ← 教材
├── pyproject.toml           ← uv 管理
└── uv.lock
```

リポジトリの方は：
- **プロジェクトモジュール名 `config/`** にリネーム済み（第1章 1-4 の理由）
- **`pyproject.toml` + `uv.lock`** で依存管理（`requirements.txt` ではなく）
- アプリが2つ並列 (`polls/`, `todo/`)
- `docs/` に教材を蓄積

---

# 付録 C: コマンドカンペ

```bash
# プロジェクト立ち上げ
uv add 'django>=6.0'
uv run django-admin startproject config .

# 開発サーバ
uv run python manage.py runserver
uv run python manage.py runserver 0:8000          # LAN 公開
uv run python manage.py runserver_plus            # django-extensions 版

# アプリ作業
uv run python manage.py startapp myapp
uv run python manage.py makemigrations myapp
uv run python manage.py migrate
uv run python manage.py createsuperuser

# 検査・調査
uv run python manage.py check
uv run python manage.py diffsettings
uv run python manage.py show_urls                 # django-extensions
uv run python manage.py shell_plus                # django-extensions

# 静的ファイル
uv run python manage.py collectstatic
uv run python manage.py findstatic polls/style.css

# テスト
uv run python manage.py test
uv run python manage.py test polls.tests.QuestionIndexViewTests.test_no_questions

# 本番風起動（gunicorn を入れた場合）
uv add gunicorn
uv run gunicorn config.wsgi:application -w 4 -b 0.0.0.0:8000
```

---

# 付録 D: 参考リンク

- [Writing your first Django app, part 1](https://docs.djangoproject.com/en/6.0/intro/tutorial01/) - 公式チュートリアル
- [django-admin and manage.py](https://docs.djangoproject.com/en/6.0/ref/django-admin/) - 全コマンドの公式リファレンス
- [How to deploy with WSGI](https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/) - 本番デプロイ
- [How to deploy with ASGI](https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/) - ASGI 本番デプロイ
- [django-extensions](https://django-extensions.readthedocs.io/) - `runserver_plus` 等
- [uv ドキュメント](https://docs.astral.sh/uv/) - パッケージ管理

---

ここまで完走おつかれさまでした。`django-admin startproject` から始まる Django プロジェクトの **始まり方** と **動かし方** をひと通り押さえました。次は **データベース** や **認証** など、アプリの中身を作り込む方向に進むと、ここで学んだ「サーバが動くしくみ」がより活きてきます。
