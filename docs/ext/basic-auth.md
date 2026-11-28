# MX: basic-auth — Basic 認証

**前提**: 第2部まで（2-6 の JWT ログイン、2-8 の `/api/auth/me`）。✅ 済み
**新しく必要なもの**: なし（Django Ninja に入っている部品だけで作る）
**ステップ**: 2つ

| ステップ | 問い |
| --- | --- |
| basic-auth-1 | 身分証（JWT）を使わないなら、一番かんたんな入り方は？ |
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

---

## basic-auth-2: 送った合言葉は、途中でどう見える？

**❓ この回の問い**: basic-auth-1 で、`curl -u` を付けると、毎回名前と合言葉を送って入れると分かった。
→ **その合言葉は、手紙のどこに、どんな形で書かれている？ 途中でだれかが見たら、読める？**

**作るもの**: なし（コードは書かない）。送った手紙の中身と、サーバーの手間を、自分の目で確かめる
**重要度**: ⚪ 背景知識 — Basic 認証を自分で使うことは少ない。でも「なぜ使われなくなったか」は、次のセッション認証・OAuth を選ぶ理由そのもの
**前ステップとの接続**: basic-auth-1 で作った `/api/auth/me-basic` を、外側から観察する

### 準備（毎回）

basic-auth-1 と同じ（Docker Desktop → `docker compose up -d` → `uv run python manage.py runserver`）。`basic-taro` はもう作ってあるので、作らなくてよい。

### 🔁 前回の思い出し

basic-auth-1 の ② で、正しい合言葉なのに 404 になった。原因は何だった？（「分からない」でよい）

<details><summary>答え</summary>

係が User を Ninja に返しただけで、`request.user` に書いていなかった。だからビューは名無しさん（`AnonymousUser`、`id` は `None`）で探して、0件になった。③ で係が `request.user = user` と書くようにして直した。

</details>

### 🧭 全体の中のいま

```
【curl（手紙）】→ ミドルウェア → 案内表 → Ninja → 【認証係 → 台帳】→ ビュー
  ↑ ①② はここ                                     ↑ ③ はここ
```

今日はコードを変えません。手紙の**中身**（①②）と、係が**毎回する手間**（③）を見ます。

🖼️ `docs/visual/django-inside.html` で「basic-auth-2」を押す。「▶ 盗み見た文字で送る」を流すと、どこで本人と見なされるかが光る。

### 🗺️ 今日の地図

```
① 手紙の中を見る           curl -v → Authorization 欄 → base64 -d で元に戻す
② 盗み見た文字で入れる？    その文字だけを -H で送る → 200
③ 毎回の照合は重い？        runserver の時間（ms）を JWT 版と比べる
```

### 🛠️ 先に自分で決める

Basic 認証は「毎回、合言葉を送る」。これで一番困りそうなのはどれ？ 1つ選んで、理由を一言。

- **A**: 途中で手紙を見られたら、合言葉がばれる
- **B**: 毎回、台帳で合言葉を照らし合わせるので、遅い
- **C**: どれも困らない

<details><summary>考え方</summary>

**A と B の両方が、実際に困ります。** この回は、A を ①② で、B を ③ で確かめます。

選んだものを覚えておいてください。③ の最後で、「一番困るのはどれか」をもう一度考えます。

</details>

### basic-auth-2-0. このステップの初出

**言葉**: Base64（文字の言いかえ方） / PBKDF2（合言葉のハッシュの作り方）
**道具**: `curl -v`、`base64 -d`

---

### チャンク①: 手紙の中を見る（コマンドだけ・ファイルは変えない）

**🤔 先に考える**: `curl -u basic-taro:pass12345` で送ると、手紙の `Authorization` 欄には何と書かれている？
A: `basic-taro:pass12345` がそのまま　B: だれにも読めない暗号　C: 読めない文字に見えるが、すぐ元に戻せる文字
（「分からない」でよい）

<details><summary>答え</summary>

**C**。`Basic YmFzaWMtdGFybzpwYXNzMTIzNDU=` のような文字です。読めないように見えますが、**だれでも元に戻せます**。下で、実際に戻します。

</details>

**🎯 書くもの**: (1) `-v`（手紙の中身を見せて）を付けて、basic-auth-1 と同じ住所を呼ぶ (2) 出てきた `Authorization` 欄の文字を、`base64 -d` で元に戻す

**🔬 1行ずつ分解**（初めて出る道具なので、打つ前に読む）

| 部品 | 読み方（正式名称） | 意味 | 無いと / 変えるとどうなる |
| --- | --- | --- | --- |
| `curl -v` | curl の `--verbose` | 送った手紙（`>` の行）と、返ってきた返事（`<` の行）を全部見せる | 付けないと、返事の中身だけが出る |
| `echo '文字'` | エコー | 文字を、次のコマンドに流す | — |
| `\|` | パイプ | 左の出力を、右のコマンドの入力にする | — |
| `base64 -d` | base64 の `--decode` | Base64 の文字を、元の文字に戻す | `-d` を付けないと、逆に Base64 に変える |

**✍️ 自分で書く**（1回目なので、見ながら手で打つ）

```bash
B=localhost:8000/api/auth
curl -s -v -u basic-taro:pass12345 $B/me-basic
```

出てきた行のうち、**`>` で始まる行だけ**を見ます（最初の `*` の行は、環境でちがってよい）。

```
> GET /api/auth/me-basic HTTP/1.1
> Host: localhost:8000
> Authorization: Basic YmFzaWMtdGFybzpwYXNzMTIzNDU=
> User-Agent: curl/8.7.1
> Accept: */*
```

`Authorization: Basic` の後ろの文字を、元に戻します。

```bash
echo 'YmFzaWMtdGFybzpwYXNzMTIzNDU=' | base64 -d
```

**▶️ 確かめる**

```
basic-taro:pass12345
```

✅ 検証済み: curl 8.7.1 / macOS の base64（`Host` の行は、検証では `127.0.0.1:8011`）

名前と合言葉が、**そのまま**出てきました。

**🔎 答えの見つけ方**: 「送った手紙に何が書いてあるか」は、いつでも `curl -v` の `>` の行で見られる。返事のくわしい中身は `<` の行。

**📖 しくみ**
- **何をしているか**: curl は `名前:合言葉` を1つの文字にまとめ、Base64 で言いかえて、`Authorization` 欄に書いた
- **なぜ Base64 にするのか**: 手紙の欄には、使える文字に決まりがある。合言葉に記号や日本語が入っても送れるように、決まった64種類の文字に言いかえる。**隠すためではない**
- **どういう原理で動くか**: 送る側（curl）が言いかえる → 手紙が届く → Ninja の `HttpBasicAuth`（basic-auth-1 の ① の型）が `Basic ` を外し、Base64 を元に戻し、`:` で名前と合言葉に分ける → あなたの係の `authenticate` に渡す

> 📇 **Base64** — 正式名称: **Base64**（RFC 4648）
> かみくだくと: どんな文字も、決まった64種類の文字（A〜Z・a〜z・0〜9・`+`・`/`）に言いかえるやり方。鍵は無い。だれでも元に戻せる。
> 似た言葉との違い: 暗号 = 鍵が無いと戻せない。ハッシュ = だれにも戻せない。Base64 = だれでも戻せる。
> この教材では: Basic 認証の `Authorization` 欄。2-6 で JWT の真ん中（中身）を読めたのも、JWT の中身が Base64 だったから

---

### チャンク②: 盗み見た文字で入れる？（コマンドだけ）

**🤔 先に考える**: ① で見た `YmFzaWMt...` の文字だけを知っている人がいる。名前も合言葉も知らない。この文字だけを手紙に書いて送ったら？
A: `200`（入れる）　B: `401`（入れない）　（理由を一言。「分からない」でよい）

答えは ▶️ で確かめます。

**🎯 書くもの**: `-u` を使わず、`-H` で `Authorization` 欄を**自分で書いて**送る。

**✍️ 自分で書く**（`-H` で `Authorization` 欄を書くのは、2-7 の `Bearer` に続いて2回目なので、穴うめ）

```bash
curl -s $B/me-basic -H 'Authorization: ___ ___' -w ' %{http_code}\n'
```

| 空欄 | 何を見れば埋められるか |
| --- | --- |
| 1つ目 | ① の `>` の行の、`Authorization:` のすぐ後ろの言葉（2-7 では `Bearer` だった所） |
| 2つ目 | ① の `>` の行の、その後ろの長い文字 |

<details><summary>答え合わせ</summary>

```bash
curl -s $B/me-basic -H 'Authorization: Basic YmFzaWMtdGFybzpwYXNzMTIzNDU=' -w ' %{http_code}\n'
```

</details>

**▶️ 確かめる**

```
{"user_id": 2, "bio": ""} 200
```

✅ 検証済み（`user_id` の数字は、ちがってよい）

**入れました。** サーバーには、本人が送ったのか、盗み見た人が送ったのか、見分ける方法がありません。

**🔎 答えの見つけ方**: 「この手紙は通るか」は、`-w ' %{http_code}\n'` の番号で見る（いつもの Q3）。

**🔬 1行ずつ分解**

| 部品 | 読み方（正式名称） | 意味 | 無いと / 変えるとどうなる |
| --- | --- | --- | --- |
| `-H 'Authorization: ...'` | curl の `--header` | 手紙の欄を、自分で書く。`-u` は、これを curl が代わりに作っていた | 付けないと 401 |
| `Basic` | 認証方式の名前（scheme） | 「この欄は Basic 認証の書き方です」という印 | `Bearer` にすると、係（`HttpBasicAuth`）は読めない → 401 |

**📖 しくみ**
- **何をしているか**: `-u` を使わずに、同じ手紙を手で作った
- **なぜ入れるのか**: 係が見ているのは「手紙に書かれた名前と合言葉」だけ。だれが書いたかは分からない。**文字を知っていれば、だれでも本人になれる**
- **どういう原理で困るのか**: Basic 認証は毎回この文字を送る → 手紙が通る道のどこか（Wi-Fi・会社のネットワーク・途中の機械）で見られたら終わり → しかも Base64 なので、合言葉そのものもばれる。ほかのサイトで同じ合言葉を使っていたら、そちらも危ない

> 🔓 **教材用の簡略化**: この教材は `http://localhost` で試している。手紙は自分の Mac の中から出ないので、途中で見られることはない。
> **本番では**: 手紙を道の途中で読めないように包む **HTTPS** が必ず要る。Basic 認証の決まり（RFC 7617）にも「HTTPS などと一緒に使わないと安全ではない」と書いてある。HTTPS は `web-security` で扱う。
> 根拠: https://www.rfc-editor.org/rfc/rfc7617#section-4

**🧪 壊してみる**: Base64 の文字を、自分で作ってみる。`printf` と `echo`、どちらで作っても同じ文字になる？ 予想してから打つ。

```bash
printf 'basic-taro:pass12345' | base64
echo 'basic-taro:pass12345' | base64
```

```
YmFzaWMtdGFybzpwYXNzMTIzNDU=
YmFzaWMtdGFybzpwYXNzMTIzNDUK
```

✅ 検証済み

**最後だけちがいます。** `echo` は、文字の最後に「改行」を足すからです。`echo` で作ったほう（`...NDUK`）を ② の手紙に入れて送ると、`{"detail": "Unauthorized"} 401` になります（合言葉が `pass12345` + 改行 になるため。確かめ済み）。**名前と合言葉が分かれば、だれでも正しい文字を作れる**ことも分かりました。

---

### チャンク③: 毎回の照合は重い？（runserver のターミナルを見る）

**🤔 先に考える**: 同じ人のプロフィールを3回ずつ取る。Basic 版（`/me-basic`）と JWT 版（`/me`）、1回にかかる時間が長いのはどっち？ 何倍くらい？
（「分からない」でよい）

<details><summary>答え</summary>

**Basic 版が、だいたい100倍くらい長い**（検証では Basic 版 約95 ms、JWT 版 約1 ms）。下で、自分の数字を見ます。

</details>

**🎯 書くもの**: (1) Basic 版を3回呼ぶ (2) ログインして身分証を `ACCESS` に入れる (3) JWT 版を3回呼ぶ。そのあと、runserver のターミナルで、各行の最後の `(○○ ms)` を比べる。

**✍️ 自分で書く**

(1) は、① で打った `curl -u` から `-v` を外し、`-o /dev/null`（返事を捨てる）を付けて3回打つ（3回目に出る形なので、日本語だけ）。

<details><summary>答え</summary>

```bash
curl -s -o /dev/null -u basic-taro:pass12345 $B/me-basic
```

これを3回。

</details>

(2)(3) は、2-6 ④の形の穴うめ:

```bash
ACCESS=$(curl -s -X POST $B/login -H "Content-Type: application/json" \
  -d '{"username": "___", "password": "___"}' \
  | uv run python -c "import json, sys; print(json.load(sys.stdin)['access'])")
curl -s -o /dev/null $B/me -H "Authorization: ___ $ACCESS"
```

| 空欄 | 何を見れば埋められるか |
| --- | --- |
| 1つ目・2つ目 | `basic-taro` の名前と合言葉（同じ人で比べる） |
| 3つ目 | 2-7 で身分証を送ったときの言葉（② の `Basic` の所に入っていたもの） |

最後の `curl` は3回打つ。

**▶️ 確かめる**: runserver のターミナル（2-5 で作った、時間を測るミドルウェアの行）

```
GET /api/auth/me-basic -> 200 (93.1 ms)
GET /api/auth/me-basic -> 200 (95.8 ms)
GET /api/auth/me-basic -> 200 (100.2 ms)
POST /api/auth/login -> 200 (143.2 ms)
GET /api/auth/me -> 200 (1.2 ms)
GET /api/auth/me -> 200 (1.0 ms)
GET /api/auth/me -> 200 (0.9 ms)
```

✅ 検証済み（DB は SQLite で確認。数字はパソコンでちがってよい。**差の大きさ**を見る）

**🔎 答えの見つけ方**: 「1回の手紙にどれだけ時間がかかったか」は、runserver のターミナルの `-> 200 (○○ ms)` の行。2-5 のミドルウェアが測っている。

**🔬 読み方**

| 行 | 何に時間を使ったか |
| --- | --- |
| `me-basic` 約95 ms × 3 | **毎回**、届いた合言葉をハッシュにして、台帳の値と比べた |
| `login` 約143 ms × 1 | 合言葉を照らし合わせたのは、ここで**1回だけ** |
| `me` 約1 ms × 3 | 身分証の署名を確かめ、台帳から本人を1回引いただけ。合言葉は使っていない |

**📖 しくみ**
- **何をしているか**: 合言葉の照合にかかる時間を、2つのやり方で比べた
- **なぜ照合は遅いのか**: Django は合言葉を **PBKDF2** というやり方でハッシュにする。同じ計算を **100万回** くり返す（Django 5.2 の決まり）。**わざと遅くしてある**。台帳が盗まれても、合言葉を1つずつ試すのに時間がかかるようにするため
- **どういう原理で差が出るか**: Basic 版は、手紙が来るたびに「100万回の計算」をする → 呼ぶ回数だけ重くなる。JWT 版は、ログインのとき1回だけ計算する → あとは署名を確かめて、台帳から本人を引くだけ

```
Basic:  手紙 → 100万回 → 返事     手紙 → 100万回 → 返事     手紙 → 100万回 → 返事
JWT:    ログイン → 100万回 → 身分証   手紙 → 署名だけ → 返事   手紙 → 署名だけ → 返事
```

> 📇 **PBKDF2** — 正式名称: **PBKDF2**（Password-Based Key Derivation Function 2）。Django では `PBKDF2PasswordHasher`
> かみくだくと: 合言葉をハッシュにするやり方の1つ。同じ計算を何度もくり返して、わざと時間をかける。
> 似た言葉との違い: ふつうのハッシュ（SHA-256 だけ）= 一瞬で終わる。PBKDF2 = それを100万回くり返す。
> この教材では: 台帳 `accounts_user` の `password` 列が `pbkdf2_sha256$1000000$...` で始まる。真ん中の `1000000` が回数
> 根拠: https://docs.djangoproject.com/en/5.2/topics/auth/passwords/

**🛠️ の答え合わせ**: 一番困るのは **A（ばれる）** です。B（遅い）は、サーバーを増やせば何とかなります。でも、ばれた合言葉は取り返せません。しかも Basic 認証には**ログアウトが無い**ので、止める方法は「合言葉を変える」しかありません。

---

### basic-auth-2-9. 終わり

**✏️ 自分で地図を描く**（今回は、箱の数だけ）。3つの箱に、「何をしたか・何が分かったか」を一言ずつ書く。

```
① ＿＿＿＿＿＿＿＿＿＿＿＿　→ 分かったこと: ＿＿＿＿＿＿＿＿＿＿＿＿
② ＿＿＿＿＿＿＿＿＿＿＿＿　→ 分かったこと: ＿＿＿＿＿＿＿＿＿＿＿＿
③ ＿＿＿＿＿＿＿＿＿＿＿＿　→ 分かったこと: ＿＿＿＿＿＿＿＿＿＿＿＿
```

<details><summary>答え合わせ</summary>

```
① curl -v で手紙の中を見た       → 合言葉は Base64 で、だれでも元に戻せる
② その文字だけを -H で送った     → 文字を知っていれば、だれでも本人になれる
③ ms を JWT 版と比べた           → 毎回 100万回の計算をするので、約100倍遅い
```

</details>

**📝 ひとこと**: 「〜だと思っていたけど、実は〜」を1行。`docs/notes.md` に貯める。
（例: 「読めない文字だから暗号だと思っていたけど、実は Base64 で、だれでも戻せた」）

**✅ できるようになったこと**
- [ ] `curl -v` で、送った手紙の中身を見られる
- [ ] Base64・暗号・ハッシュのちがいを、「戻せるのはだれか」で説明できる
- [ ] Basic 認証が使われなくなった理由を2つ言える（ばれやすい・毎回重い）

**⏭️ 次の問い**: 合言葉を見せるのは、**最初の1回だけ**にしたい。2回目からは合言葉なしで、「さっきの人だ」と窓口に覚えておいてもらうには？（JWT のように本人に身分証を持たせる以外の方法で）

---
🩺 詰まったら: Q1 動いてる？ / Q2 何て言ってる？ / Q3 呼んだら返事は来る？ のどれから聞く？
❓ 分からない言葉があれば `?: <言葉>` と送ってください。そこだけ説明して、`docs/_glossary.md` に追記します。
▶ **次**: `MX: session-auth` — 窓口に覚えておいてもらう（セッション認証）
