# MX: session-auth — セッション認証

**前提**: `basic-auth`（`/api/auth/me-basic` ができている）。✅ 済み
**新しく必要なもの**: なし（Django 標準の `django.contrib.sessions` と、Ninja の `django_auth` を使う）
**ステップ**: 3つ

| ステップ | 問い |
| --- | --- |
| session-auth-1 | 合言葉を見せるのは最初の1回だけにして、あとは窓口に覚えておいてもらうには？ |
| session-auth-2 | ログアウトすると、何が消える？ JWT とどうちがう？ |
| session-auth-3 | Cookie はブラウザが勝手に送る。ほかのサイトから悪用されたら？（CSRF） |

---

## session-auth-1: 窓口に覚えておいてもらう

**❓ この回の問い**: basic-auth-2 で、Basic 認証は毎回合言葉を送るので、ばれやすく、毎回重い（約95 ms）と分かった。
→ **合言葉を見せるのは最初の1回だけにして、2回目からは窓口に「さっきの人だ」と覚えておいてもらうには？**

**作るもの**: (1) ログインすると Cookie を渡す API（`POST /api/auth/session/login`） (2) その Cookie だけで、自分のプロフィールが返る API（`GET /api/auth/me-session`）
**重要度**: 🔴 毎日使う — ブラウザで使う Web アプリのログインは、ほとんどこの形。Django の管理画面もこれで動いている
**前ステップとの接続**: `/me`（JWT）・`/me-basic`（Basic）の横に、セッション版を足す。どれも残す

> 🧒 **かみくだくと**: **セッション認証**は、最初の1回だけ合言葉を見せる入り方。窓口は「この人はログイン済み」という**控え**を台帳（`django_session`）に書き、本人には**控えの番号**だけを渡す。2回目からは番号を見せるだけでよい。

### 準備（毎回）

basic-auth と同じ（Docker Desktop → `docker compose up -d` → `uv run python manage.py runserver`）。試す人は `basic-taro` を使う。

### 🔁 前回の思い出し

2-6 のおわりに、セッション認証と JWT を表で比べた。セッション認証では、サーバーは「だれがログイン中か」をどこに覚えていた？（「分からない」でよい）

<details><summary>答え</summary>

`django_session` という台帳（テーブル）に1行書いて覚える。本人には Cookie の `sessionid` を渡す。JWT は、サーバーは何も覚えない（行は増えない）。
今日は、この表のとおりになるかを自分の手で確かめます。

</details>

### 🧭 全体の中のいま

```
curl → 【ミドルウェア（Cookie を見て本人を入れる）】→ 案内表 → Ninja → 【認証係 django_auth】→ ビュー → ORM → 【MySQL django_session】
```

basic-auth では、ミドルウェアは `request.user` に名無しさんを入れていました。今日は、**ミドルウェアが Cookie を見て、本人を入れる**ようになります。

🖼️ `docs/visual/django-inside.html` で「session-auth-1」を押す。「▶ Cookie ありで呼ぶ」を流して、どこで本人が分かるかを見る。

### 🗺️ 今日の地図

```
① ログインの窓口を作る      accounts/api.py   合言葉が合えば auth.login() → 控えを書き、番号を渡す
② セッション版の窓口を作る  accounts/api.py   auth=django_auth を付ける
③ 番号の行き来を見る        コマンドだけ       Set-Cookie → Cookie → django_session の1行
```

### 🛠️ 先に自分で決める

2回目から「さっきの人だ」と分かってもらうには、何を渡す？ 1つ選んで、理由を一言。

- **A**: 本人に、署名付きの身分証を持たせる。窓口は何も覚えない
- **B**: 窓口が控えを持つ。本人には控えの番号だけ渡す
- **C**: やっぱり毎回、合言葉を見せる

<details><summary>考え方</summary>

**A は JWT**（2-6 で作った）、**C は Basic**（前回まで）。今日作るのは **B のセッション認証**です。

A と B のちがいは「**覚えているのはだれか**」です。A は本人が持ち歩く。B は窓口が覚えている。この1つのちがいが、次の session-auth-2（ログアウト）で大きな差になります。

</details>

### session-auth-1-0. このステップの初出

**Django / Ninja**: `auth.login()`（控えを書いて番号を渡す） / `django_auth`（Ninja のセッション認証の係）
**道具**: `curl -c`（Cookie をしまう）・`curl -b`（Cookie を送る）

---

### チャンク①: ログインの窓口を作る（`accounts/api.py`）

> ⚠️ 書いている途中で保存すると、runserver が途中の状態を読んで止まることがあります。止まったら、直して保存し直す。それでも動かなければ、runserver を起動し直す。

**🤔 先に考える**: JWT の `login`（2-6）は、合言葉が合ったら身分証を作って返した。セッション版は、合言葉が合ったら何をすればよい？
A: 身分証を作って返す　B: 窓口が控えを書いて、番号を渡す　（🛠️ を思い出す。「分からない」でよい）

<details><summary>答え</summary>

**B**。Django では、`auth.login(request, user)` の1行がそれをやります。控えを `django_session` に書き、番号を Cookie にして返事に付けます。

</details>

**🎯 書くもの**: JWT の `login` 関数とほぼ同じ窓口 `session_login` を、`get_my_profile_basic` のすぐ下に足す。合言葉を照らし合わせる3行は同じ。最後だけちがう: 身分証を作る代わりに `auth.login(request, user)` を呼び、`user` を返す。

**✍️ 自分で書く**（穴うめ。上の3行は、JWT の `login` 関数からそのまま写してよい）

ファイルの一番上、`from django.contrib.auth import authenticate` のすぐ上に1行（basic-auth-1 の `auth.py` と同じ1行）:

```python
from django.contrib import ___
```

`get_my_profile_basic` のすぐ下（`@router.patch("/me"` の上）に:

```python
@router.post("/session/login", response={200: UserOut, 401: ErrorOut})
def session_login(request: HttpRequest, payload: LoginIn):
    user = authenticate(request, username=payload.username, password=payload.password)
    if user is None:
        return Status(401, {"detail": "ユーザー名かパスワードが違います"})
    auth.___(request, ___)
    return ___
```

| 空欄 | 何を見れば埋められるか |
| --- | --- |
| 1つ目 | `accounts/auth.py` の1行目 |
| 2つ目・3つ目 | 🤔 の答え（`auth.login(request, user)`） |
| 4つ目 | 返すのは、ログインした人（`response` の `200: UserOut` が、id と username を返す形） |

<details><summary>答え合わせ（差分。前後2行つき）</summary>

```diff
+from django.contrib import auth
 from django.contrib.auth import authenticate
 from django.db import transaction
 from django.http import HttpRequest
```

```diff
 def get_my_profile_basic(request: HttpRequest):
     return get_object_or_404(Profile, user_id=request.user.id)


+@router.post("/session/login", response={200: UserOut, 401: ErrorOut})
+def session_login(request: HttpRequest, payload: LoginIn):
+    user = authenticate(request, username=payload.username, password=payload.password)
+    if user is None:
+        return Status(401, {"detail": "ユーザー名かパスワードが違います"})
+    auth.login(request, user)
+    return user
+
+
 @router.patch("/me", response=ProfileOut, auth=JWTAuth())
 def update_my_profile(request: HttpRequest, payload: ProfileIn):
```

</details>

> 🐍 **Python注**: このファイルには、JWT 用の関数 `login` がもうある。`from django.contrib.auth import login` と書くと、名前がぶつかって下の関数に上書きされる。だから `auth.login` と、箱の名前を付けて呼ぶ。

**▶️ 確かめる**: 正しい合言葉と、まちがった合言葉で1回ずつ。

```bash
B=localhost:8000/api/auth
curl -s -X POST $B/session/login -H 'Content-Type: application/json' \
  -d '{"username": "basic-taro", "password": "pass12345"}' -w ' %{http_code}\n'
curl -s -X POST $B/session/login -H 'Content-Type: application/json' \
  -d '{"username": "basic-taro", "password": "x"}' -w ' %{http_code}\n'
```

```
{"id": 2, "username": "basic-taro"} 200
{"detail": "ユーザー名かパスワードが違います"} 401
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / django-ninja 1.7.1（DB は SQLite で確認。`id` の数字は、ちがってよい）

2行目の `ユ...` は、日本語の「ユーザー名かパスワードが違います」を、文字の番号で書いたものです。こわれてはいません。

**🔎 答えの見つけ方**: ログインで何が起きたかは、runserver のターミナルの SQL を見る。`INSERT INTO django_session` が出ていれば、控えが書かれた。

**🔬 1行ずつ分解**（新しく出た行だけ。ほかは 2-6 の `login` と同じ）

| 部品 | 読み方（正式名称） | 意味 | 無いと / 変えるとどうなる |
| --- | --- | --- | --- |
| `from django.contrib import auth` | 認証の部品の箱 | `auth.login` を呼ぶために、箱ごと読む | 消すと、ログインを呼ぶたびに 500（`NameError: name 'auth' is not defined`） |
| `auth.login(request, user)` | `django.contrib.auth.login()` | 控えを `django_session` に書き、番号（`sessionid`）を返事の Cookie に付ける | 消すと、200 は返るが番号が届かない（③の 🧪） |
| `return user` | 戻り値 | ログインした人を返す。`UserOut` の形（id・username）になる | — |

**📖 しくみ**
- **何をしているか**: 合言葉が合ったら、窓口が「この人はログイン済み」と控えを書いた
- **なぜ必要か**: 控えがあれば、2回目からは合言葉を見なくても、番号を見るだけで本人と分かる
- **どういう原理で動くか**: `auth.login()` が呼ばれる → Django が新しい番号（ランダムな32文字）を作る → `django_session` に「番号・中身（だれか）・期限」の1行を書く → 返事に `Set-Cookie: sessionid=番号` を付ける

> 📇 **`login()`** — 正式名称: **`django.contrib.auth.login(request, user)`**
> かみくだくと: 「この人をログイン済みにして」と Django に頼む命令。控えを書いて、番号を渡す。
> 似た言葉との違い: `authenticate()` = 合言葉が合うか確かめるだけ（何も覚えない）。`login()` = 確かめたあとで、覚えてもらう。
> この教材では: `session_login` の中。JWT の `login` 関数（窓口の名前）とは別物

---

### チャンク②: セッション版の窓口を作る（`accounts/api.py`）

**🤔 先に考える**: basic-auth-1 では、ミドルウェアが `request.user` に名無しさんを入れていたので、係が本人を書き込む必要があった。セッション版の係も、本人を書き込む必要がある？
A: ある　B: ない　（理由を一言。「分からない」でよい）

<details><summary>答え</summary>

**B（ない）**。名無しさんになったのは「Cookie（セッション）が無いから」でした（basic-auth-1 の ② の 📖）。今回は Cookie があるので、**ミドルウェアが最初から本人を入れてくれます**。Ninja の係 `django_auth` は、それを確かめるだけです。

</details>

**🎯 書くもの**: `/me-basic` とそっくりな窓口 `/me-session` を、`session_login` のすぐ下に足す。ちがうのは2つだけ: 住所が `/me-session`、係が `django_auth`（`()` は付けない。もう作ってある係だから）。係は `ninja.security` から読み込む。

**✍️ 自分で書く**（`/me` の形の窓口は3回目なので、日本語だけで書く。止まったらヒントを開ける）

<details><summary>ヒント1: 使う部品の名前</summary>

- 読み込み: `from ninja.security import django_auth`（`from ninja_jwt.authentication import JWTAuth` のすぐ上）
- 窓口: `/me-basic` の3行を写して、住所・関数名・`auth=` を変える。関数名は `get_my_profile_session`

</details>

<details><summary>ヒント2: 骨組み</summary>

```python
@router.get("/me-session", response=ProfileOut, auth=___)
def get_my_profile_session(request: HttpRequest):
    return get_object_or_404(Profile, user_id=request.user.id)
```

</details>

<details><summary>答え合わせ（差分。前後2行つき）</summary>

```diff
 from ninja import Field, Router, Schema, Status  # Field を追加
+from ninja.security import django_auth
 from ninja_jwt.authentication import JWTAuth  # 追加
 from ninja_jwt.exceptions import TokenError
```

```diff
     auth.login(request, user)
     return user


+@router.get("/me-session", response=ProfileOut, auth=django_auth)
+def get_my_profile_session(request: HttpRequest):
+    return get_object_or_404(Profile, user_id=request.user.id)
+
+
 @router.patch("/me", response=ProfileOut, auth=JWTAuth())
```

</details>

**▶️ 確かめる**: Cookie を付けずに呼ぶ。

```bash
curl -s $B/me-session -w ' %{http_code}\n'
```

```
{"detail": "Unauthorized"} 401
```

✅ 検証済み

番号（Cookie）を見せていないので、401 です。番号を付けて呼ぶのは ③ でやります。

**🔎 答えの見つけ方**: `django_auth` の中身は `.venv/lib/python3.14/site-packages/ninja/security/session.py` の `class SessionAuth`。`request.user.is_authenticated` を見ているだけの、とても短い係です。

**🔬 1行ずつ分解**（新しく出た部品だけ）

| 部品 | 読み方（正式名称） | 意味 | 無いと / 変えるとどうなる |
| --- | --- | --- | --- |
| `from ninja.security import django_auth` | Ninja のセッション認証の係 | もう作ってある係（`SessionAuth()`）を読む | 消すと、起動の時点で `NameError` |
| `auth=django_auth` | 認証クラス（authentication class） | この窓口に、セッションの係を付ける。`BasicAuth()` とちがい `()` は付けない（もう作ってある実物だから） | 消すと、だれでも呼べてしまう |

**📖 しくみ**
- **何をしているか**: Cookie の番号で本人と分かったら通す窓口を作った
- **なぜ係のコードを書かなくてよいか**: 番号から本人を探す仕事は、Django のミドルウェアがもうやっている。係は「本人が分かったか」を見るだけ
- **どういう原理で動くか**: リクエストが来る → `SessionMiddleware` が Cookie の `sessionid` を読む → `AuthenticationMiddleware` が、その番号の控えから本人を探して `request.user` に入れる → Ninja が `django_auth` を呼ぶ → 係は `request.user.is_authenticated`（ログイン済みか）を見る → 本人なら通す、名無しさんなら 401

> 📇 **`django_auth`** — 正式名称: **`ninja.security.django_auth`**（`SessionAuth` クラスの実物）
> かみくだくと: 「ミドルウェアが本人を見つけてくれたか」を確かめるだけの係。
> 似た言葉との違い: `BasicAuth()` = 自分で合言葉を照らし合わせる係。`JWTAuth()` = 身分証の署名を確かめる係。`django_auth` = 照らし合わせはミドルウェアに任せる係。
> この教材では: `/api/auth/me-session` の `auth=`

---

### チャンク③: 番号の行き来を見る（コマンドだけ）

**🤔 先に考える**: ログインの返事に付いてくる番号（Cookie）を、curl にしまっておいて、次の呼び出しで見せる。`/me-session` の返事は何になる？ 1回にかかる時間は、Basic 版（約95 ms）と比べてどう？
（「分からない」でよい。答えは ▶️ で）

**🎯 書くもの**: (1) `-i` で、ログインの返事の見出し（ヘッダー）を見る (2) `-c` で番号をファイルにしまってログイン (3) `-b` でその番号を見せて `/me-session` を呼ぶ (4) 台帳の控えをのぞく

**🔬 1行ずつ分解**（初めて出る道具なので、打つ前に読む）

| 部品 | 読み方（正式名称） | 意味 |
| --- | --- | --- |
| `curl -i` | curl の `--include` | 返事の見出し（ヘッダー）も一緒に見せる |
| `curl -c ファイル` | curl の `--cookie-jar` | 返事で受け取った Cookie を、ファイルにしまう |
| `curl -b ファイル` | curl の `--cookie` | ファイルにしまった Cookie を、リクエストに付けて送る |

**✍️ 自分で書く**（1回目なので、見ながら手で打つ）

```bash
curl -s -i -X POST $B/session/login -H 'Content-Type: application/json' \
  -d '{"username": "basic-taro", "password": "pass12345"}'
```

`Set-Cookie` の行だけを見ます（長いので一部を省略）。

```
Set-Cookie:  csrftoken=agqE4dun...; expires=...; Max-Age=31449600; Path=/; SameSite=Lax
Set-Cookie:  sessionid=rltakyh7efdt1cjlh2dbbfkaw016cyhe; expires=Sat, 12 Dec 2026 01:48:49 GMT; HttpOnly; Max-Age=1209600; Path=/; SameSite=Lax
```

`sessionid=` の後ろが**控えの番号**です。`csrftoken` は session-auth-3 で使います。今は気にしなくてよい。

次に、番号をファイルにしまってログインし、その番号で呼びます。

```bash
C=/tmp/session-taro.txt
curl -s -c $C -X POST $B/session/login -H 'Content-Type: application/json' \
  -d '{"username": "basic-taro", "password": "pass12345"}' -w ' %{http_code}\n'
curl -s -b $C $B/me-session -w ' %{http_code}\n'
curl -s -b $C $B/me-session -w ' %{http_code}\n'
```

**▶️ 確かめる**

```
{"id": 2, "username": "basic-taro"} 200
{"user_id": 2, "bio": ""} 200
{"user_id": 2, "bio": ""} 200
```

runserver のターミナル:

```
POST /api/auth/session/login -> 200 (95.5 ms)
GET /api/auth/me-session -> 200 (1.3 ms)
GET /api/auth/me-session -> 200 (1.2 ms)
```

✅ 検証済み（DB は SQLite で確認。数字はちがってよい。**差の大きさ**を見る）

**合言葉を送ったのはログインの1回だけ**です。2回目からは番号だけで入れて、しかも Basic 版の約100分の1の時間でした。

最後に、台帳の控えをのぞきます。

```bash
uv run python manage.py shell -c "
from django.contrib.sessions.models import Session
for s in Session.objects.all(): print(s.session_key[:8], s.get_decoded())"
```

```
pezs9lvc {'_auth_user_id': '2', '_auth_user_backend': 'django.contrib.auth.backends.ModelBackend', '_auth_user_hash': '78f3fbfb...'}
rltakyh7 {'_auth_user_id': '2', '_auth_user_backend': 'django.contrib.auth.backends.ModelBackend', '_auth_user_hash': '78f3fbfb...'}
```

✅ 検証済み（最初の行に `20 objects imported automatically` などが出てもよい）

ログインを2回したので、控えも2行あります。`_auth_user_id: '2'` が「この番号は 2 番の人」という中身です。

**🔎 答えの見つけ方**: 「どんな Cookie を送ったか」は `curl -v` の `> Cookie:` の行。「サーバーが何を覚えているか」は、上の `Session.objects.all()`。

**📖 しくみ**
- **何をしているか**: 番号を受け取り、しまい、見せた。サーバーの台帳には、番号ごとの控えが残っている
- **なぜ速いか**: 2回目からは、合言葉のハッシュ（100万回の計算）をしない。SQL を3本引くだけ（控え → 本人 → プロフィール）
- **どういう原理で動くか**: ログインの返事の `Set-Cookie` で、番号が届く → ブラウザ（今回は `-c` のファイル）がしまう → 次から同じサイトへのリクエストに `Cookie: sessionid=番号` が付く → サーバーは番号で `django_session` を引き、`_auth_user_id` から本人を探す

> 📇 **Cookie** — 正式名称: **HTTP Cookie**（`Set-Cookie` ヘッダーで渡し、`Cookie` ヘッダーで返ってくる）
> かみくだくと: サーバーが「次から、これを付けてきて」と渡す小さなメモ。ブラウザがしまっておき、同じサイトに行くたびに**自動で**付けて送る。
> 似た言葉との違い: `Authorization` ヘッダー = 送る側が毎回、自分で付ける。Cookie = 一度もらえば、ブラウザが勝手に付ける。
> この教材では: `sessionid`（控えの番号）と `csrftoken`（session-auth-3 で使う）

**🧪 壊してみる**: ① の `auth.login(request, user)` の1行を消して保存する。ログインは何番が返る？ そのあと `/me-session` は？ 予想してから打つ。

```bash
C2=/tmp/session-taro2.txt
curl -s -i -c $C2 -X POST $B/session/login -H 'Content-Type: application/json' \
  -d '{"username": "basic-taro", "password": "pass12345"}'
curl -s -b $C2 $B/me-session -w ' %{http_code}\n'
```

```
HTTP/1.1 200 OK
...
{"id": 2, "username": "basic-taro"}
{"detail": "Unauthorized"} 401
```

✅ 検証済み

**読み方**: ログインは 200 なのに、`Set-Cookie: sessionid=` の行がありません。合言葉は合っていた（`authenticate()` は通った）のに、控えを書いていないので番号が届かない。だから次は 401 です（① の分解表の `auth.login` の行）。**確かめたら、`auth.login(request, user)` を戻す。**

---

### session-auth-1-9. 終わり

**✏️ 自分で地図を描く**（箱の数だけ）。3つの箱に「何を・なぜ」を一言ずつ書く。

```
① ＿＿＿＿＿＿＿＿＿＿＿＿　何を: ＿＿＿＿＿＿＿＿＿＿　なぜ: ＿＿＿＿＿＿＿＿＿＿
② ＿＿＿＿＿＿＿＿＿＿＿＿　何を: ＿＿＿＿＿＿＿＿＿＿　なぜ: ＿＿＿＿＿＿＿＿＿＿
③ ＿＿＿＿＿＿＿＿＿＿＿＿　何を: ＿＿＿＿＿＿＿＿＿＿　なぜ: ＿＿＿＿＿＿＿＿＿＿
```

<details><summary>答え合わせ</summary>

```
① ログインの窓口       何を: 合言葉が合えば auth.login() で控えを書く   なぜ: 2回目から合言葉を見ないため
② セッション版の窓口   何を: auth=django_auth を付ける                  なぜ: 本人探しはミドルウェアがやるので、確かめるだけでよい
③ 番号の行き来を見た   何を: Set-Cookie → Cookie → django_session        なぜ: 窓口が覚えていることを、目で確かめるため
```

</details>

**📝 ひとこと**: 「〜だと思っていたけど、実は〜」を1行。`docs/notes.md` に貯める。
（例: 「ログインは合言葉を確かめることだと思っていたけど、実は確かめたあとに『覚えてもらう』のが本体だった」）

**✅ できるようになったこと**
- [ ] `authenticate()` と `login()` のちがいを説明できる
- [ ] Set-Cookie で番号が届き、次から Cookie で送られる流れを説明できる
- [ ] セッション認証が Basic より速い理由を言える（合言葉の計算はログインの1回だけ）

**⏭️ 次の問い**: 窓口は控えを持っている。では、**ログアウトしたら控えはどうなる？** JWT はログアウトしても、渡した身分証が5分間使えた。セッションは？

---
🩺 詰まったら: Q1 動いてる？ / Q2 何て言ってる？ / Q3 呼んだら返事は来る？ のどれから聞く？
❓ 分からない言葉があれば `?: <言葉>` と送ってください。そこだけ説明して、`docs/_glossary.md` に追記します。
▶ **次**: `MX: session-auth 2` — ログアウトすると、何が消える？
