# MX: basic-auth — Basic 認証

**前提**: 第2部まで（2-6 の JWT ログイン、2-8 の `/api/auth/me`）。✅ 済み
**新しく必要なもの**: なし（Django Ninja に入っている部品だけで作る）
**ステップ**: 2つ（この回は1つ目）

| ステップ | 問い |
| --- | --- |
| basic-auth-1 | 身分証（JWT）を使わないなら、一番かんたんな入り方は？ ← **この回** |
| basic-auth-2 | 毎回送っている合言葉は、途中でどう見える？ |

---

## basic-auth-1: 毎回、名前と合言葉で入る

**❓ この回の問い**: 2-6 では「先にログインして身分証（JWT）をもらい、毎回それを見せる」形を作った。
→ **では、身分証を使わないなら、一番かんたんな入り方は？**

答えの予想: 「毎回、名前と合言葉をそのまま見せる」。これが **Basic 認証** です。この回で作って確かめます。

**作るもの**: 名前と合言葉を毎回送ると、自分のプロフィールが返る API（`GET /api/auth/me-basic`）
**重要度**: 🟡 読めればよい — 自分の API で使うことは少ない。社内ツールや、開発中の画面を一時的に隠すときに出会う
**前ステップとの接続**: 2-8 の `/api/auth/me`（JWT 版）の横に、Basic 認証版を足す。JWT 版はそのまま残す

> 🧒 **かみくだくと**: **Basic 認証**は、窓口に来るたびに「名前と合言葉」を言う入り方。身分証は作らない。窓口は毎回、台帳（`accounts_user`）を引いて合言葉を照らし合わせる。

### 準備（毎回）

1. Docker Desktop を起動する
2. `docker compose up -d`（MySQL を起こす）
3. 別のターミナルで `uv run python manage.py runserver`
4. 試す人を1人作る（もう作ってあれば `409` が返る。それでよい）

```bash
curl -s -X POST localhost:8000/api/auth/register -H 'Content-Type: application/json' \
  -d '{"username": "basic-taro", "password": "pass12345"}' -w ' %{http_code}\n'
```

```
{"id": 2, "username": "basic-taro"} 201
```

`id` の数字は、ちがってよい。

### 🔁 前回の思い出し

2-7 で `auth=JWTAuth()` を付けた。この係は、ビュー関数より**前に**何をしていた？（「分からない」でよい）

<details><summary>答え</summary>

身分証（JWT）の署名と期限を確かめる。合っていれば、台帳から User を引いて **`request.user` に入れる**。だからビューで `request.user.id` と書けた。
この答えは、チャンク③でもう一度使います。

</details>

### 🧭 全体の中のいま

```
curl → ミドルウェア → 案内表（URL）→ Ninja → 【認証係】→ 担当職員（ビュー）→ ORM → MySQL
                                              ↑ 今日はここ
```

認証係は、ビュー関数より前に Ninja が呼ぶ係です（2-7 の `auth=`）。今日は、この係を**自分で作ります**。

🖼️ `docs/visual/django-inside.html` をブラウザで開き、「全体」→「basic-auth-1」の順に押す。光った「認証係」をクリックすると説明が出る。

### 🗺️ 今日の地図

```
① 認証係を作る          accounts/auth.py（新しく作る）
② 窓口に係を付ける      accounts/api.py   → なぜか 404 になる
③ 係が名前を書き込む    accounts/auth.py  → 200 になる
```

### 🛠️ 先に自分で決める

「名前と合言葉を確かめる仕事」を、どこに書く？ 1つ選んで、理由を一言。

- **A**: ビュー関数の中に、毎回書く
- **B**: 確かめる係を別のファイルに作り、窓口に `auth=` で付ける

<details><summary>考え方</summary>

**B** にします。JWT のときと同じ形です。

- 係を1つ作れば、どの窓口にも `auth=BasicAuth()` と付けるだけで使える。A だと、窓口ごとに同じ照合を書くことになる
- ビュー関数は「プロフィールを返す」だけに集中できる。だれが来たかの確認は、係に任せる

A を選んでも、まちがいではありません。窓口が1つなら動きます。窓口が増えると困ります。

</details>

### basic-auth-1-0. このステップの初出

**Django / Ninja**: `HttpBasicAuth`（Ninja の Basic 認証の型） / **道具**: `curl -u`

---

### チャンク①: 認証係を作る（`accounts/auth.py`・新規）

**🤔 先に考える**: 係は、名前と合言葉を受け取ります。合っていたら何を返せば、Ninja は「通してよい」と分かる？
A: `True`　B: その人の User　（「分からない」でよい）

<details><summary>答え</summary>

**B（その人の User）**。Ninja は「何か返ってきたら通す。`None` なら 401」と決めています。User を返せば、通してよい印になり、だれかも伝わります。合わないとき、Django の `authenticate()` は `None` を返します。

</details>

**🎯 書くもの**: `accounts/` の中に `auth.py` を新しく作る。Ninja の `HttpBasicAuth` を土台にして、名前と合言葉を Django に照らし合わせてもらう係 `BasicAuth` を書く。

**🔬 1行ずつ分解**（初めて出る形なので、打つ前に読む）

`from django.contrib import auth`

| 部品 | 読み方（正式名称） | 意味 | 無いと / 変えるとどうなる |
| --- | --- | --- | --- |
| `django.contrib` | ジャンゴ コントリブ | Django に付いてくる部品の置き場 | — |
| `import auth` | 認証の部品（`django.contrib.auth`） | 2-6 で使った `authenticate()` が入っている箱を、箱ごと読む | 消すと、下の `auth.authenticate` で `NameError` |

`from ninja.security import HttpBasicAuth`

| 部品 | 読み方（正式名称） | 意味 | 無いと / 変えるとどうなる |
| --- | --- | --- | --- |
| `ninja.security` | ニンジャ セキュリティ | Ninja の認証係の置き場。2-7 の `JWTAuth` の親戚もここ | — |
| `HttpBasicAuth` | エイチティーティーピー ベーシック オース | Basic 認証の**型**。届いた手紙から名前と合言葉を取り出す仕事は、もう書いてある | — |

`class BasicAuth(HttpBasicAuth):`

| 部品 | 読み方（正式名称） | 意味 | 無いと / 変えるとどうなる |
| --- | --- | --- | --- |
| `class BasicAuth` | クラス定義 | 自分の係の名前 | 名前を変えると、②で付けるときの名前も変わる |
| `(HttpBasicAuth)` | 継承 | 型の仕事を受け継ぐ。足りない「照合」だけを自分で書く | 消すと、ただの空のクラス。Ninja が係として使えない |

`def authenticate(self, request, username, password):`

| 部品 | 読み方（正式名称） | 意味 | 無いと / 変えるとどうなる |
| --- | --- | --- | --- |
| `def authenticate` | メソッド定義 | 型が「ここだけは書いて」と空けている場所。名前は決まっている | 名前を変えると、起動の時点で止まる: `TypeError: Can't instantiate abstract class BasicAuth without an implementation for abstract method 'authenticate'`（型が空けた場所が、空のまま） |
| `username, password` | 引数 | 型が取り出した名前と合言葉が、ここに入ってくる | — |

`return auth.authenticate(request, username=username, password=password)`

| 部品 | 読み方（正式名称） | 意味 | 無いと / 変えるとどうなる |
| --- | --- | --- | --- |
| `auth.authenticate(...)` | Django の `authenticate()` | 台帳を引き、合言葉を照らし合わせる。合えば User、合わなければ `None` | — |
| `return` | 戻り値 | 結果を Ninja に渡す。User なら通す、`None` なら 401 | 消すと、いつも `None`。正しい合言葉でも 401 |

> 🐍 **Python注**: メソッドの名前も `authenticate`、呼ぶ関数も `authenticate`。`auth.` を付けて呼ぶので、ぶつからない。`auth.` は「`auth` の箱の中の」という意味。

**✍️ 自分で書く**（1回目なので、下を**見ながら手で打つ**。コピペはしない）

```python
from django.contrib import auth
from ninja.security import HttpBasicAuth


class BasicAuth(HttpBasicAuth):
    def authenticate(self, request, username, password):
        return auth.authenticate(request, username=username, password=password)
```

✅ 検証済み: Python 3.14.3 / Django 5.2.17 / django-ninja 1.7.1

**▶️ 確かめる**: 設定とファイルに打ちまちがいが無いかを、Django に点検してもらう。

```bash
uv run python manage.py check
```

```
System check identified no issues (0 silenced).
```

この時点では、まだどの窓口にも付けていません。打ちまちがいが無いことだけを確かめます。

**🔎 答えの見つけ方**: `HttpBasicAuth` が中で何をしているかは、`.venv/lib/python3.14/site-packages/ninja/security/http.py` を開くと読めます（`class HttpBasicAuth` で検索）。

**📖 しくみ**
- **何をしているか**: 「名前と合言葉が合うか」を確かめる係を作った
- **なぜ必要か**: 窓口ごとに照合を書かずに済むように、係にまとめる（🛠️ の B）
- **どういう原理で動くか**: 窓口に係が付いていると、リクエストが来るたびに Ninja が係を呼ぶ → 型（`HttpBasicAuth`）が手紙の `Authorization` という欄から名前と合言葉を取り出す → あなたの `authenticate` を呼ぶ → 返ってきた値を Ninja が見て、通すか 401 かを決める

> 📇 **HttpBasicAuth** — 正式名称: **`ninja.security.HttpBasicAuth`**
> かみくだくと: Basic 認証の係の「型」。手紙から名前と合言葉を取り出すところまでは型がやる。照らし合わせ方だけ、自分で書く。
> 似た言葉との違い: `JWTAuth` = 身分証（JWT）を確かめる係。`HttpBasicAuth` = 名前と合言葉を確かめる係の型。
> この教材では: `accounts/auth.py` の `BasicAuth` の親

---

### チャンク②: 窓口に係を付ける（`accounts/api.py`）

> ⚠️ 書いている途中で保存すると、runserver が途中の状態を読んで止まることがあります。止まったら、直して保存し直す。それでも動かなければ、runserver を起動し直す。

**🤔 先に考える**: 窓口を付けたら、`basic-taro` の正しい合言葉で呼びます。返事の番号はどれ？
A: `200`　B: `401`　C: `404`　（理由を一言。「分からない」でよい）

答えは ▶️ で、実際に打って確かめます。

**🎯 書くもの**: 2-8 の `get_my_profile`（`/me`）のすぐ下に、そっくりな窓口 `/me-basic` を足す。ちがうのは2つだけ: 住所が `/me-basic`、係が `BasicAuth()`。係は ① のファイルから読み込む。

**✍️ 自分で書く**（`/me` の窓口を書くのは2回目なので、穴うめ）

ファイルの上の方、`from .models import ...` のすぐ上に1行:

```python
from .auth import ___
```

`get_my_profile` の関数のすぐ下（`@router.patch("/me"` の上）に4行:

```python
@router.get("/me-basic", response=ProfileOut, auth=___)
def get_my_profile_basic(request: HttpRequest):
    return get_object_or_404(Profile, user_id=request.user.___)
```

| 空欄 | 何を見れば埋められるか |
| --- | --- |
| 1つ目 | ① で作ったクラスの名前 |
| 2つ目 | すぐ上の `/me` の `auth=` の書き方。係の名前だけ入れ替える（`()` を忘れずに） |
| 3つ目 | すぐ上の `get_my_profile` の最後の行 |

<details><summary>答え合わせ（差分。前後2行つき）</summary>

```diff
 from ninja_jwt.tokens import RefreshToken

+from .auth import BasicAuth
 from .models import Profile, User  # 追加

 # ログインまわりの API 一式。URL の頭（/auth）は config/api.py で決める
```

```diff
     # user_id は一意なので、見つかるのは0件か1件
     return get_object_or_404(Profile, user_id=request.user.id)


+@router.get("/me-basic", response=ProfileOut, auth=BasicAuth())
+def get_my_profile_basic(request: HttpRequest):
+    return get_object_or_404(Profile, user_id=request.user.id)
+
+
 @router.patch("/me", response=ProfileOut, auth=JWTAuth())
 def update_my_profile(request: HttpRequest, payload: ProfileIn):
```

</details>

**▶️ 確かめる**: 3回呼ぶ。`-u 名前:合言葉` は「この名前と合言葉で Basic 認証して」と curl に頼む書き方。

```bash
B=localhost:8000/api/auth
curl -s $B/me-basic -w ' %{http_code}\n'
curl -s -u basic-taro:wrong $B/me-basic -w ' %{http_code}\n'
curl -s -u basic-taro:pass12345 $B/me-basic -w ' %{http_code}\n'
```

```
{"detail": "Unauthorized"} 401
{"detail": "Unauthorized"} 401
{"detail": "Not Found: No Profile matches the given query."} 404
```

✅ 検証済み（DB は SQLite で確認。番号と返事の中身は同じになる）

**正しい合言葉なのに、404**。予想は当たりましたか？ 1行目と2行目の 401 は、係がちゃんと止めています。

**🔎 答えの見つけ方**: なぜ 404 かは、runserver のターミナルに出た **SQL** を見る。最後の `SELECT` の `WHERE` を読みます。

```
SELECT ... FROM `accounts_profile` WHERE `accounts_profile`.`user_id` IS NULL LIMIT 21
```

（MySQL では名前が `` ` `` で囲まれて出る。SQLite で確かめたときは `"` で囲まれていた。中身は同じ）

`user_id IS NULL`。「持ち主が空っぽのプロフィール」を探していました。つまり **`request.user.id` が空** です。

**🔬 1行ずつ分解**（新しく出た部品だけ。ほかは 2-8 の `/me` と同じ）

| 部品 | 読み方（正式名称） | 意味 | 無いと / 変えるとどうなる |
| --- | --- | --- | --- |
| `from .auth import BasicAuth` | 相対 import | 同じアプリの `auth.py` から係を読む | 消すと、起動の時点で止まる: `NameError: name 'BasicAuth' is not defined` |
| `auth=BasicAuth()` | 認証クラス（authentication class） | この窓口に、① の係を付ける | `()` を忘れると、起動はするが、呼ぶたびに 500: `TypeError: AuthBase.__init__() takes 1 positional argument but 2 were given`。係そのものではなく、係の作り方（クラス）を渡してしまうため |
| `curl -u 名前:合言葉` | curl の `--user` | curl が名前と合言葉を Basic 認証の形にして送る | 付けないと、名前も合言葉も送らない → 401 |

**📖 しくみ**
- **何をしているか**: 窓口 `/me-basic` に係を付けた。係は正しく通した。でも、ビューが「だれか」を知らない
- **なぜ 404 か**: ビューは `request.user` を見ている。でも、① の係は User を **Ninja に返しただけ**。`request.user` には何も書いていない
- **どういう原理で動くか**: ミドルウェアの `AuthenticationMiddleware` が、ビューより先に `request.user` を用意する → Cookie（セッション）が無いので「名無しさん」（`AnonymousUser`）を入れる → 名無しさんの `id` は `None` → `user_id IS NULL` で探す → 0件 → 404

---

### チャンク③: 係が名前を書き込む（`accounts/auth.py`）

**🤔 先に考える**: 🔁 の答えを思い出す。`JWTAuth` は、確かめたあと User をどこに入れていた？ 同じことを ① の係にもさせると、②の 404 はどうなる？（一言で）

<details><summary>答え</summary>

`request.user` に入れていた。① の係も同じことをすれば、ビューの `request.user.id` に本人の番号が入る → 200 になる。

</details>

**🎯 書くもの**: ① の `return auth.authenticate(...)` の1行を、3つに分ける。(1) 結果を `user` にしまう (2) `user` が `None` でなければ、`request.user` に入れる (3) `user` を返す。

**✍️ 自分で書く**（穴うめ。① の1行を消して、この4行に置きかえる）

```python
        user = auth.authenticate(request, username=username, password=password)
        if user is not ___:
            request.___ = user
        return ___
```

| 空欄 | 何を見れば埋められるか |
| --- | --- |
| 1つ目 | 合わないとき `authenticate()` が返すもの（① の 🤔 の答え） |
| 2つ目 | ビューが読んでいる場所（② の 📖） |
| 3つ目 | Ninja に渡すもの（① の 🤔 の答え） |

<details><summary>答え合わせ（差分。前後2行つき）</summary>

```diff
 class BasicAuth(HttpBasicAuth):
     def authenticate(self, request, username, password):
-        return auth.authenticate(request, username=username, password=password)
+        user = auth.authenticate(request, username=username, password=password)
+        if user is not None:
+            request.user = user
+        return user
```

</details>

<details><summary>変更後の全文（答え合わせ用）</summary>

```python
from django.contrib import auth
from ninja.security import HttpBasicAuth


class BasicAuth(HttpBasicAuth):
    def authenticate(self, request, username, password):
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            request.user = user
        return user
```

</details>

**▶️ 確かめる**: ② と同じ3行を、もう一度打つ。

```
{"detail": "Unauthorized"} 401
{"detail": "Unauthorized"} 401
{"user_id": 2, "bio": ""} 200
```

✅ 検証済み（DB は SQLite で確認。`user_id` の数字は、ちがってよい）

3行目が **200** になりました。JWT 版の `/me` も、今までどおり動きます（確かめ済み）。

**🔎 答えの見つけ方**: runserver のターミナルで、3行目の SQL の `WHERE` が `user_id = 2` に変わったことを見る。番号が入れば、本人のプロフィールが見つかる。

**🔬 1行ずつ分解**

| 部品 | 読み方（正式名称） | 意味 | 無いと / 変えるとどうなる |
| --- | --- | --- | --- |
| `user = auth.authenticate(...)` | 代入 | 照合の結果を `user` にしまう。User か `None` | — |
| `if user is not None:` | `None` との比較 | 合言葉が合ったときだけ、次の行に進む | 消すと、合わないときに `request.user` が `None` になる |
| `request.user = user` | リクエストの属性 | ビューが読む場所に、本人を書く。`JWTAuth` も中で同じことをしている | 消すと、② の 404 に戻る |
| `return user` | 戻り値 | Ninja に「通してよい」を伝える | 消すと 401（下の 🧪） |

**📖 しくみ**
- **何をしているか**: 係が、確かめた本人を `request.user` に書き込むようにした
- **なぜ必要か**: Ninja の決まりでは、係の返した値は `request.auth` に入る。でも、このアプリのビューは `request.user` を読む。JWT 版と同じ場所に入れれば、ビューは**どちらの係が付いていても同じ書き方**でよい
- **どういう原理で動くか**: リクエストが来る → ミドルウェアが名無しさんを `request.user` に入れる → Ninja が係を呼ぶ → 係が照合して、本人で**上書き**する → ビューが `request.user.id` を読む → 本人の番号で探せる

**🧪 壊してみる**: `return user` の1行を消して保存する。正しい合言葉で呼ぶと、番号は何になる？ 予想してから打つ。

```bash
curl -s -u basic-taro:pass12345 $B/me-basic -w ' %{http_code}\n'
```

```
{"detail": "Unauthorized"} 401
```

runserver のターミナル:

```
GET /api/auth/me-basic -> 401 (100.0 ms)
Unauthorized: /api/auth/me-basic
```

✅ 検証済み

**読み方**: 最後の行 `Unauthorized: /api/auth/me-basic` は「Ninja : この住所で、通してよい印が無かった」。`return` が無いと、Python の関数は `None` を返します。Ninja は `None` を見て 401 にしました（分解表の `return user` の行）。**確かめたら、`return user` を戻す。**

---

### basic-auth-1-9. 終わり

**✏️ 自分で地図を描く**（穴埋め）。空欄を埋めて、各箱に「何を・なぜ」を一言ずつ書く。

```
① ＿＿＿ を作る          accounts/auth.py   何を: ＿＿＿＿＿＿  なぜ: ＿＿＿＿＿＿
② 窓口に ＿＿＿ で付ける  accounts/api.py    何を: ＿＿＿＿＿＿  なぜ: ＿＿＿＿＿＿
③ 係が ＿＿＿ に書き込む  accounts/auth.py   何を: ＿＿＿＿＿＿  なぜ: ＿＿＿＿＿＿
```

<details><summary>答え合わせ</summary>

```
① 認証係を作る              何を: 名前と合言葉を Django に照らし合わせる   なぜ: 窓口ごとに書かないため
② 窓口に auth= で付ける     何を: /me-basic に BasicAuth() を付ける         なぜ: ビューより前に確かめるため
③ 係が request.user に書く  何を: 確かめた本人を入れる                     なぜ: ビューが読む場所だから（JWT と同じ）
```

</details>

**📝 ひとこと**: 「〜だと思っていたけど、実は〜」を1行。書いたら `docs/notes.md` に貯める。
（例: 「係が通してくれたら、ビューは本人が分かると思っていたけど、実は `request.user` に書くのは係の仕事だった」）

**✅ できるようになったこと**
- [ ] Basic 認証が「毎回、名前と合言葉を送る」入り方だと説明できる
- [ ] 係の返り値が User なら通る・`None` なら 401、と予想できる
- [ ] 404 のとき、SQL の `WHERE` を見て原因を探せる

**⏭️ 次の問い**: `curl -u` は、名前と合言葉を手紙のどこに、どんな形で書いて送っている？ **途中でだれかがその手紙を見たら、合言葉は読める？**

---
🩺 詰まったら: Q1 動いてる？ / Q2 何て言ってる？ / Q3 呼んだら返事は来る？ のどれから聞く？
❓ 分からない言葉があれば `?: <言葉>` と送ってください。そこだけ説明して、`docs/_glossary.md` に追記します。
▶ **次**: `MX: basic-auth 2` — 送った合言葉は、途中でどう見える？
