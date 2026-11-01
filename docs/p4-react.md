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


---

## 第4部-2: OpenAPI から型を作る

**❓ この回の問い**: 4-1 では、商品の型（`Product`）を手で書いた。Django 側の `ProductOut` には、3-7 で `review_count` と `rating_avg` が増えているのに、手書きの型は知らない。Django を直すたびに、TypeScript の型も手で直し続ける？

**作るもの**: Ninja の OpenAPI（1-8）から TypeScript の型ファイル `frontend/src/api/schema.d.ts` を自動で作り、商品一覧に星の平均を足す
**重要度**: 🟡 よく使う — 画面と API の食い違いを、ブラウザで開く前に `npm run build` で見つけられる
**前ステップとの接続**: 1-8 の `/api/openapi.json` を、そのまま材料にする。4-1 の `App.tsx` の手書きの型を置き換える

### 2-0. このステップの初出

**Django / Ninja**: なし（1-8 の OpenAPI を使い回す） / **Python**: なし

画面側の道具として、openapi-typescript を1つだけ使います。

> 🧒 **かみくだくと**: **openapi-typescript** は、OpenAPI の説明書（JSON）を読んで、TypeScript の型だけを書き出す道具。動くコードは作らない。`fetch` は今までどおり自分で書く。

### 2-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

**① 型を作るコマンドを足す**

`frontend/package.json` の `"scripts"` の、`"lint": "oxlint",` の下に1行

```json
    "gen:api": "npx -y -p typescript@5.9.3 -p openapi-typescript@7.13.0 openapi-typescript http://127.0.0.1:8000/api/openapi.json -o src/api/schema.d.ts",
```

✅ 検証済み: openapi-typescript 7.13.0 / TypeScript 5.9.3（npx が一時的に入れる）

`npm install` ではなく `npx -p` で動かしているのには、理由があります（2-2 の「なぜ npx か」）。

Django の開発サーバを動かしたまま、`frontend/` で実行します。

```bash
npm run gen:api
```

```text
✨ openapi-typescript 7.13.0
🚀 http://127.0.0.1:8000/api/openapi.json → src/api/schema.d.ts [54.5ms]
```

✅ 検証済み: 約1,080行の `src/api/schema.d.ts` ができる

できたファイルの中から、`ProductOut` を探してみてください。Django の `ProductOut` と同じ並びです。

```ts
        ProductOut: {
            /** Id */
            id: number;
            /** Name */
            name: string;
            /** Price */
            price: string;
            /** Category Id */
            category_id: number;
            /** Stock */
            stock: number;
            /** Review Count */
            review_count: number;
            /** Rating Avg */
            rating_avg: number | null;
        };
```

✅ 検証済み: Django 5.2.17 / django-ninja 1.7.1 の `/api/openapi.json` から生成

見てほしいのは3か所です。

- `price` は `string`。Django の `Decimal` は、JSON では `"2980.00"` のような文字列になる（3-1）
- `stock` は、`alias="inventory.quantity"` ではなく、項目名の `stock` で出ている
- `rating_avg` は `number | null`。レビューが無い商品では `null` になる（3-7）

ファイルの先頭には「自動で作ったので、直接いじらない」と書かれています。直したいときは Django 側を直して、`npm run gen:api` を流し直します。

**② 手書きの型を置き換える**

`frontend/src/App.tsx` の1行目の下に1行

```tsx
import type { components } from './api/schema'
```

`type Product = { ... }` の7行（コメント含む）を、次の2行に置き換える

```tsx
// 1件の商品。Ninja の ProductOut から自動で作った型を使う
type Product = components['schemas']['ProductOut']
```

**③ 壊れるのを見る**

星の平均を表示したいので、`<li>` の中身を次のように変えます。

```tsx
            {p.name} — {p.price} 円（在庫 {p.stock}）★{p.rating_avg.toFixed(1)}
```

```bash
npm run build
```

```text
src/App.tsx(27,51): error TS18047: 'p.rating_avg' is possibly 'null'.
```

✅ 検証済み: TypeScript 7.0.2（`tsc -b`）

ブラウザで開く前に、「レビューの無い商品では `null` になるよ」と TypeScript が止めてくれました。Django 側の `rating_avg: float | None` が、そのまま型として届いています。

**④ 直す**

`<li>` の中身を、`null` のときは「レビューなし」と出すように変えます。

```tsx
          <li key={p.id}>
            {p.name} — {p.price} 円（在庫 {p.stock}）
            {p.rating_avg === null
              ? ' レビューなし'
              : ` ★${p.rating_avg.toFixed(1)}（${p.review_count}件）`}
          </li>
```

✅ 検証済み: `npm run build`・`npm run lint` が通る

`npm run dev` で開くと、こうなります（`scripts/seed.py` のデータ）。

```text
商品一覧
・Django 入門 — 2980.00 円（在庫 15） ★4.3（3件）
・Python ノート — 450.50 円（在庫 0） ★3.0（1件）
・TypeScript 実践ガイド — 3520.00 円（在庫 8） ★5.0（1件）
・SQL 図鑑 — 2200.00 円（在庫 3） レビューなし
…
```

✅ 検証済み: Chromium（Playwright）で表示し、Console のエラーが0件

`src/api/schema.d.ts` もコミットします。中身は自動で作ったものですが、入れておけば Django を動かしていなくても `npm run build` が通ります。

### 2-2. 🔬 仕組み解剖

| | openapi-typescript（`npm run gen:api`） |
| --- | --- |
| 正式名称 | openapi-typescript。OpenAPI 3.0 / 3.1 の JSON から、TypeScript の型（`paths` と `components`）を書き出す |
| いつ・誰が | **自分が `npm run gen:api` を流したときだけ**。Django を直しても、型は勝手には変わらない |
| 発行される SQL | なし（`/api/openapi.json` を1回読むだけ） |
| TS での対応物 | これ自体が TS 側の道具。Prisma の `prisma generate`（DB の定義から型を作る）と同じ考え方 |
| なぜこの設計 | Ninja は、`Schema` の宣言から OpenAPI を作る（1-8）。それを型に変えれば、「API の形」を書くのは Django 側の1か所だけで済む |
| 失敗すると | Django が動いていないと `ResolveError: fetch failed` で止まり、ファイルは作られない（前のファイルが残る） |

✅ 検証済み: openapi-typescript 7.13.0
根拠: https://openapi-ts.dev/introduction

```text
  shop/api.py の ProductOut（Python）
        |  Ninja が宣言から作る（1-8）
        v
  /api/openapi.json（説明書）
        |  npm run gen:api（openapi-typescript）
        v
  src/api/schema.d.ts の components["schemas"]["ProductOut"]（TypeScript）
        |  import type
        v
  App.tsx の Product
```

✅ 検証済み: ①②

**型は「流したときの写真」**

`schema.d.ts` は、流したときの API の形を写したものです。Django 側で `ProductOut` の `stock` を `quantity` に変えても、流し直すまでは `npm run build` は通ります。流し直すと、使っている場所で止まります。

```text
src/App.tsx(27,42): error TS2339: Property 'stock' does not exist on type '{ id: number; name: string; price: string; category_id: number; quantity: number; review_count: number; rating_avg: number | null; }'.
```

✅ 検証済み: `shop/api.py` の `stock` を `quantity` に変えて、流し直す前は通り、流し直した後に止まる（確かめたあと元に戻した）

だから、**Django の `Schema` を変えたら `npm run gen:api`** を習慣にします。

**なぜ `npm install` ではなく `npx -p` か**

この画面は TypeScript 7 で作りました（4-1）。openapi-typescript 7.13.0 は、TypeScript 5 の部品を使って型のファイルを書き出すので、TypeScript 5 を求めます。そのまま `npm install -D openapi-typescript` すると、npm が断ります。

```text
npm error Could not resolve dependency:
npm error peer typescript@"^5.x" from openapi-typescript@7.13.0
```

✅ 検証済み: npm 11.20.0 / Node.js 26.13.0

`--legacy-peer-deps` で無理に入れると、型を作る途中で落ちます（TypeScript 7 には、openapi-typescript が使う `ts.factory` が無い）。

```text
TypeError: Cannot read properties of undefined (reading 'createKeywordTypeNode')
```

✅ 検証済み: `--legacy-peer-deps` で入れて `openapi-typescript` を流して確認

`npx -p typescript@5.9.3 -p openapi-typescript@7.13.0` は、この2つを**プロジェクトの外の一時的な場所**に入れて動かします。画面の型チェック（TypeScript 7）と、型を作る道具（TypeScript 5）が混ざりません。版も固定しているので、誰が流しても同じファイルになります。
根拠: https://docs.npmjs.com/cli/v11/commands/npx

### 2-3. 🐍 Python注

新しい文法はありません。

TypeScript の側で、2つだけ補足します。

- `import type { ... }` は、「型だけ使う」読み込み。ビルド後の JavaScript からは消える。この画面の設定（`tsconfig.app.json` の `verbatimModuleSyntax`）では、型だけのものは `import type` で書く決まり
- `p.rating_avg === null ? ... : ...` の `:` の側では、TypeScript が `p.rating_avg` を `number` として扱う（**絞り込み**、narrowing）。だから `.toFixed(1)` が書ける

根拠: https://www.typescriptlang.org/docs/handbook/2/narrowing.html

### 2-4. 解説 — なぜこう設計するか

手書きの型は、**間違っていてもビルドが通ります**。たとえば手で `rating_avg: number` と書くと、`npm run build` は通り、ブラウザではレビューの無い商品で `null.toFixed` になって、画面が真っ白になります。

```text
TypeError: Cannot read properties of null (reading 'toFixed')
```

✅ 検証済み: 手書きの型に `rating_avg: number` と書いて、ビルドが通り、Chromium で画面が空になるのを確認

型を自動で作れば、`null` になりうることを Django 側（`float | None`）が知らせてくれます。API の形の「正」は Django の `Schema` で、TypeScript の型はそこから写すだけ、という役割分担です。

🧠 Django の考え方: Ninja は「型を書けば、検証も説明書も付いてくる」（1-4・1-8）。その説明書は、人が読むだけでなく、画面側の型の材料にもなる。

### 2-5. ⚠️ アンチパターン ／ 🔓 教材用の簡略化

> ⚠️ **アンチパターン**: 自動で作った `schema.d.ts` を手で直す。次に `npm run gen:api` を流すと、直した分が消える。直したいなら Django の `Schema` を直す。
> 根拠: 生成されたファイルの先頭に `Do not make direct changes to the file.` とある（✅ 検証済み）

> 🔓 **教材用の簡略化**: 型の材料を、動いている Django（`http://127.0.0.1:8000`）から取っている。
> **本番では**: CI などでサーバを起動せずに作りたいときは、Ninja の `export_openapi_schema` コマンドで JSON をファイルに書き出し、そのファイルから型を作る。このコマンドは、`INSTALLED_APPS` に `"ninja"` を足すと使えるようになる（✅ 検証済み: 書き出した JSON から作った型は、①と同じファイルになった）。
> 根拠: https://django-ninja.dev/guide/openapi/

### 2-6. 🔮 予測 → 動作確認

1. Django を止めたまま `npm run gen:api` を流したら？ 前の `schema.d.ts` はどうなる？
2. `import type { components }` を `import { components }`（`type` なし）にしたら？
3. 2-2 のように Django 側で `stock` を `quantity` に変えたあと、`npm run gen:api` を**流さずに** `npm run dev` で開いたら？

<details><summary>答え</summary>

1. `ResolveError: fetch failed` で止まる。ファイルは書き換わらず、前のものが残る（検証済み）
2. `npm run build` が止まる。`components` は型なので、`verbatimModuleSyntax` の設定では `import type` が要る（検証済み: `error TS1484: 'components' is a type and must be imported using a type-only import when 'verbatimModuleSyntax' is enabled.`）
3. ビルドは通るが、画面の「在庫」が空になる。API は `quantity` を返すのに、画面は `p.stock` を読んでいて、`undefined` になるから（検証済み: 全商品が「在庫 ）」になり、Console にエラーも出ない）。型は流したときの写真なので、流し直さないと食い違いに気づけない

</details>

### 2-7. ✅ 想起チェック

1. `schema.d.ts` を作り直すのは、どんなとき？
2. 生成された型で `price` が `number` ではなく `string` なのはなぜ？

<details><summary>答え</summary>

1. Django の `Schema`（応答や入力の形）を変えたとき。`npm run gen:api` を流す
2. Django の `Decimal` は、誤差を出さないために JSON では文字列（`"2980.00"`）で返すから（3-1）

</details>

### 2-8. 📇 まとめカード

この回で覚えることは1つだけ: **画面の型は手で書かず、Ninja の OpenAPI から `npm run gen:api` で作る。Django の `Schema` を変えたら、流し直す。**

📒 用語集に追記: openapi-typescript / 型の生成 / `import type` / 絞り込み（narrowing）

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第4部 ステップ3` — 記事の一覧・詳細画面
