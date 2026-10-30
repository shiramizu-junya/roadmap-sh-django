# 第4部 — React から叩く

> これまでと同じく、1周目で全部分からなくて大丈夫です。
> 分からない箇所には `# TODO: わからん` と残して、先に進んでください。

---

## 第4部-1: CORS

**❓ この回の問い**: 第3部で、API は一通りそろった。今までは `curl` と Swagger UI で叩いてきた。では、React の画面（別のポートで動く開発サーバ）から `fetch` したら、そのまま読める？

**作るもの**: `frontend/`（Vite + React + TypeScript）に商品一覧の画面を1つ作り、Django 側で CORS を許して表示させる
**重要度**: 🔴 毎日使う — 画面と API を別々に動かす構成では、最初に必ずぶつかる
**前ステップとの接続**: 3-7 の `GET /api/products` を、ブラウザの画面から呼ぶ。2-5 のミドルウェアを1つ足す

### 1-0. このステップの初出

**Django / Ninja**: django-cors-headers（`CORS_ALLOWED_ORIGINS`） / **Python**: なし

> 🧒 **かみくだくと**: **オリジン**（origin）は、「どこから来たページか」の住所。`http://localhost:5173` のように、**方式・ホスト・ポート**の3つの組。1つでも違えば、別のオリジン。

> 🧒 **かみくだくと**: **CORS**（Cross-Origin Resource Sharing、オリジン間リソース共有）は、「別のオリジンのページに、応答を読ませてよいか」を**サーバが応答のヘッダで伝える**仕組み。読ませるか決めるのはブラウザ。許可のヘッダが無ければ、ブラウザが応答を捨てる。

### 1-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

**① React の画面を作る**（リポジトリ直下で実行）

```bash
npm create vite@9.3.3 frontend -- --template react-ts --no-interactive
cd frontend
npm install
```

✅ 検証済み: Node.js 26.13.0 / create-vite 9.3.3（Vite 8.3.5・React 19.3.1・TypeScript 7.0.2 が入る）

`frontend/.gitignore` も一緒にでき、`node_modules` はコミットされません。

`frontend/src/App.tsx` を、全文置き換える

```tsx
import { useEffect, useState } from 'react'

// 1件の商品（4-2 で、Ninja の OpenAPI から自動で作る型に置き換える）
type Product = {
  id: number
  name: string
  price: string
  stock: number
}

const API_URL = 'http://127.0.0.1:8000/api'

function App() {
  const [products, setProducts] = useState<Product[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    fetch(`${API_URL}/products`)
      .then((res) => res.json())
      .then((data: Product[]) => setProducts(data))
      .catch((e: unknown) => setError(String(e)))
  }, [])

  return (
    <main>
      <h1>商品一覧</h1>
      {error && <p>読み込めませんでした: {error}</p>}
      <ul>
        {products.map((p) => (
          <li key={p.id}>
            {p.name} — {p.price} 円（在庫 {p.stock}）
          </li>
        ))}
      </ul>
    </main>
  )
}

export default App
```

✅ 検証済み: TypeScript 7.0.2（`npm run build`・`npm run lint` も通過）

React の書き方は、既に知っているとおりです。この教材の主役は Django 側なので、画面の解説はしません。

**② 壊れるのを見る**

Django の開発サーバ（`uv run python manage.py runserver`）を動かしたまま、別のターミナルで画面を起動します。

```bash
cd frontend
npm run dev
```

ブラウザで `http://localhost:5173/` を開くと、「読み込めませんでした: TypeError: Failed to fetch」と出ます。開発者ツールの Console には、次のエラーです。

```text
Access to fetch at 'http://127.0.0.1:8000/api/products' from origin 'http://localhost:5173' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

✅ 検証済み: Chromium（Playwright）で表示して確認（検証時は API のポートだけ変えた）

ところが、Django のログには `"GET /api/products HTTP/1.1" 200` が出ています。**リクエストは届き、Django は正しく返している**のです。止めたのはブラウザです。

**③ CORS を許す**

```bash
uv add django-cors-headers
```

✅ 検証済み: django-cors-headers 4.9.0

`config/settings.py` を3か所直す。`INSTALLED_APPS` の `"django.contrib.staticfiles",` の下に1行

```python
    "corsheaders",  # 追加: 別のオリジン（React の開発サーバ）からの呼び出しを許す
```

`MIDDLEWARE` の `timing_middleware` の行の下に1行

```python
    "corsheaders.middleware.CorsMiddleware",  # 追加: 応答を作る CommonMiddleware より前に置く
```

ファイルの最後に追加

```python
# 呼び出しを許すオリジン（React の開発サーバ）。ここに無いオリジンからは、ブラウザが応答を読ませない
CORS_ALLOWED_ORIGINS = ["http://localhost:5173"]
```

✅ 検証済み: Django 5.2.17（ruff・mypy も通過。テストは何も変えずに全部通る）

コミットするときは、`frontend/` と、`uv add` で変わった `pyproject.toml`・`uv.lock` も一緒に入れます。

Django を再起動して、ブラウザを再読み込みします。

```text
商品一覧
・Django 入門 — 2980.00 円（在庫 5）
・Python ノート — 450.50 円（在庫 0）
```

✅ 検証済み: Chromium で表示し、Console のエラーが0件

`curl` でヘッダを見ると、違いが分かります。

```bash
curl -s -i -H "Origin: http://localhost:5173" http://127.0.0.1:8000/api/products | grep -i access-control
curl -s -i -H "Origin: http://example.com" http://127.0.0.1:8000/api/products | grep -i access-control
```

```text
access-control-allow-origin: http://localhost:5173
```

✅ 検証済み: 1本目だけヘッダが付く。2本目（許していないオリジン）は何も出ない

### 1-2. 🔬 仕組み解剖

| | django-cors-headers（`CORS_ALLOWED_ORIGINS`） |
| --- | --- |
| 正式名称 | django-cors-headers（サードパーティのアプリ）。`CorsMiddleware` と設定 `CORS_ALLOWED_ORIGINS` |
| いつ・誰が | リクエストごとに `CorsMiddleware` が、ヘッダの `Origin` を見る。一覧にあれば、応答に `Access-Control-Allow-Origin` を足す。判定して応答を捨てるのは**ブラウザ** |
| 発行される SQL | なし（HTTP のヘッダだけの話） |
| TS での対応物 | Express の `cors` ミドルウェアと同じ役目 |
| なぜこの設計 | ブラウザは、ログイン中のサイトの Cookie などを自動で送る。どのページからでも読めると、悪いサイトがあなたの名前でデータを読める。だから「読ませてよいオリジン」をサーバが決める |
| 失敗すると | 許していないオリジンなら、Django は 200 を返すが、ブラウザが捨てて `Failed to fetch`。`CorsMiddleware` を `CommonMiddleware` より後ろに置くと、先に応答が作られた場合にヘッダが付かない |

✅ 検証済み: django-cors-headers 4.9.0 / Django 5.2.17

```text
  page (http://localhost:5173)  -- fetch, Origin: http://localhost:5173 -->  Django
  Django  -- 200 + JSON (no Access-Control-Allow-Origin) -->  browser drops it (Failed to fetch)
  Django  -- 200 + JSON + Access-Control-Allow-Origin: http://localhost:5173 -->  page reads it
```

✅ 検証済み: ②③

見てほしいのは、どちらの場合も Django は 200 を返している点です。CORS は**サーバの守り**ではなく、**ブラウザが利用者を守る**ための決まりです。`curl` は CORS を気にしないので、②のときも読めました。

**ヘッダ付きの POST は、先に「下見」が来る**

`Authorization` ヘッダを付けた注文（`POST /api/orders`）のような呼び出しでは、ブラウザが本番の前に `OPTIONS` で「このヘッダとメソッドで送ってよいか」を尋ねます（**プリフライト**、preflight）。django-cors-headers は、これにも答えます。

```text
access-control-allow-origin: http://localhost:5173
access-control-allow-headers: accept, authorization, content-type, user-agent, x-csrftoken, x-requested-with
access-control-allow-methods: DELETE, GET, OPTIONS, PATCH, POST, PUT
access-control-max-age: 86400
```

✅ 検証済み: `curl -X OPTIONS` に `Access-Control-Request-Method: POST` と `Access-Control-Request-Headers: authorization, content-type` を付けて確認
根拠: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS#preflighted_requests

> ⏭️ **後で回収**: プリフライトが実際に飛ぶのは、4-4（ログイン画面）で `Authorization` ヘッダを付けて呼ぶとき。

### 1-3. 🐍 Python注

新しい文法はありません。

### 1-4. 解説 — なぜこう設計するか

許すオリジンは、`*`（全部）ではなく、**一覧で1つずつ**書きました。React の画面は自分たちのものなので、その住所だけ許せば足ります。本番では、画面を置くドメイン（例: `https://shop.example.com`）を足します。

🧠 Django の考え方: Django 本体に無い仕組みは、アプリとミドルウェアを足して組み込む。`INSTALLED_APPS` と `MIDDLEWARE` に1行ずつ、設定は `settings.py` に書く。

### 1-5. ⚠️ アンチパターン ／ 🔓 教材用の簡略化

> ⚠️ **アンチパターン**: 面倒だからと `CORS_ALLOW_ALL_ORIGINS = True` にする。django-cors-headers の README は、どのサイトからでも呼べてしまうので「危険になりうる」とし、`CORS_ALLOWED_ORIGINS` で絞るよう勧めている。
> 根拠: https://github.com/adamchainz/django-cors-headers#cors_allow_all_origins-bool

> 🔓 **教材用の簡略化**: 許すオリジンを `settings.py` に直接書き、`API_URL` も `App.tsx` に直接書いている。
> **本番では**: どちらも環境ごとに変わるので、環境変数から読む（Django は `.env`、Vite は `import.meta.env`）。
> 根拠: https://vite.dev/guide/env-and-mode

### 1-6. 🔮 予測 → 動作確認

1. ②のとき（CORS を許す前）、Django のログにリクエストは届いている？ ステータスは？
2. ②の Console に、同じエラーが**2回**出た。`fetch` は1回しか書いていないのに、なぜ？
3. `CORS_ALLOWED_ORIGINS` に `"http://localhost:5173/"`（最後に `/`）と書いたら？

<details><summary>答え</summary>

1. 届いている。2本とも 200（検証済み）。Django は普通に返し、ブラウザが読ませなかった
2. React の `StrictMode`（`main.tsx` で包んでいる）が、開発中だけ effect をもう1回走らせるから。本番のビルドでは1回（検証済み: 2回とも同じエラー）
   根拠: https://react.dev/reference/react/StrictMode
3. Django の起動時（システムチェック）に止まる。`(corsheaders.E014) Origin 'http://localhost:5173/' in CORS_ALLOWED_ORIGINS should not have path`（検証済み）。オリジンにはパスを付けない（方式・ホスト・ポートだけ）

</details>

### 1-7. ✅ 想起チェック

1. `http://localhost:5173` と `http://localhost:8000` は、同じオリジン？
2. CORS で応答を捨てるのは、Django とブラウザのどっち？

<details><summary>答え</summary>

1. 違う。ポートが違うので別のオリジン
2. ブラウザ。Django は許可のヘッダを付けるかどうかを決めるだけ

</details>

### 1-8. 📇 まとめカード

この回で覚えることは1つだけ: **別のオリジンの画面から呼ぶなら、django-cors-headers の `CORS_ALLOWED_ORIGINS` に、その画面のオリジンを書く。**

📒 用語集に追記: オリジン / CORS / プリフライト / `CORS_ALLOWED_ORIGINS`

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第4部 ステップ2` — OpenAPI から型を作る
