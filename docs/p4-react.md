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


---

## 第4部-3: 記事の一覧・詳細画面

**❓ この回の問い**: 第2部の記事 API には、一覧（`GET /api/posts`）と1件（`GET /api/posts/{id}`）がある。画面で「一覧 → クリックで詳細」を作るとき、無い記事の URL を開かれたら、画面はどうなる？

**作るもの**: React Router で「記事一覧」「記事詳細」「商品一覧」の3画面を切り替える。API を呼ぶ処理は `src/api/client.ts` の1か所にまとめる
**重要度**: 🟡 よく使う — 画面が2つ以上になったら必ず要る。404 の扱いは、どの画面でも同じ問題になる
**前ステップとの接続**: 2-12 のページング（`{"items", "count"}`）と、1-9 の 404（`get_object_or_404`）を画面から見る。型は 4-2 で作った `schema.d.ts` を使う

### 3-0. このステップの初出

**Django / Ninja**: なし / **Python**: なし

画面側では、React Router を使います。

> 🧒 **かみくだくと**: **React Router** は、ブラウザの URL（`/posts/3` など）を見て、どの画面（コンポーネント）を出すかを決める道具。`<Link>` で移るときは、ページを読み込み直さずに、画面だけを差し替える。

### 3-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

**① React Router を入れる**（`frontend/` で実行）

```bash
npm install react-router@8.4.0
```

✅ 検証済み: react-router 8.4.0（`package.json` の `dependencies` に `"react-router": "^8.4.0"` が入る）

`npm warn install-scripts` と出ることがありますが、Vite が使う `fsevents` の話で、React Router とは関係ありません。そのままで動きます。

**② API を呼ぶ処理を1か所にまとめる**

画面が3つになると、どの画面にも `API_URL` と `fetch` を書くことになります。1か所にまとめます。

`frontend/src/api/client.ts` を新規作成

```ts
// API の住所。画面ごとに書かず、ここ1か所にまとめる
export const API_URL = 'http://127.0.0.1:8000/api'

// GET して、返ってきた JSON を T 型として返す
export async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`)
  return (await res.json()) as T
}
```

**③ 画面を3つに分ける**

今の `App.tsx` の商品一覧は、`pages/` に移します。

`frontend/src/pages/ProductList.tsx` を新規作成（4-2 の `App.tsx` と同じ中身で、名前と `fetch` の部分だけ違う）

```tsx
import { useEffect, useState } from 'react'
import { getJson } from '../api/client'
import type { components } from '../api/schema'

// 1件の商品。Ninja の ProductOut から自動で作った型を使う
type Product = components['schemas']['ProductOut']

function ProductList() {
  const [products, setProducts] = useState<Product[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    getJson<Product[]>('/products')
      .then((data) => setProducts(data))
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
            {p.rating_avg === null
              ? ' レビューなし'
              : ` ★${p.rating_avg.toFixed(1)}（${p.review_count}件）`}
          </li>
        ))}
      </ul>
    </main>
  )
}

export default ProductList
```

`frontend/src/pages/PostList.tsx` を新規作成

```tsx
import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { getJson } from '../api/client'
import type { components } from '../api/schema'

// 記事の一覧。@paginate なので {"items": [...], "count": 全件数} の形（2-12）
type PagedPosts = components['schemas']['PagedPostOut']

function PostList() {
  const [page, setPage] = useState<PagedPosts | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getJson<PagedPosts>('/posts')
      .then((data) => setPage(data))
      .catch((e: unknown) => setError(String(e)))
  }, [])

  if (error) return <p>読み込めませんでした: {error}</p>
  if (page === null) return <p>読み込み中…</p>

  return (
    <main>
      <h1>記事一覧（{page.count}件）</h1>
      <ul>
        {page.items.map((post) => (
          <li key={post.id}>
            <Link to={`/posts/${post.id}`}>{post.title}</Link>
            {post.category && `（${post.category.name}）`}
          </li>
        ))}
      </ul>
    </main>
  )
}

export default PostList
```

`frontend/src/pages/PostDetail.tsx` を新規作成

```tsx
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router'
import { getJson } from '../api/client'
import type { components } from '../api/schema'

type Post = components['schemas']['PostOut']

function PostDetail() {
  const { postId } = useParams() // URL の /posts/:postId の部分（文字列）
  const [post, setPost] = useState<Post | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getJson<Post>(`/posts/${postId}`)
      .then((data) => setPost(data))
      .catch((e: unknown) => setError(String(e)))
  }, [postId])

  if (error) return <p>読み込めませんでした: {error}</p>
  if (post === null) return <p>読み込み中…</p>

  return (
    <main>
      <p>
        <Link to="/">← 記事一覧へ</Link>
      </p>
      <h1>{post.title}</h1>
      <p>
        {post.category?.name ?? 'カテゴリなし'} /{' '}
        {new Date(post.created_at).toLocaleString('ja-JP')}
      </p>
      <p>{post.tags.map((tag) => `#${tag.name}`).join(' ')}</p>
      <p>{post.body}</p>
    </main>
  )
}

export default PostDetail
```

`frontend/src/App.tsx` を、全文置き換える

```tsx
import { BrowserRouter, Link, Route, Routes } from 'react-router'
import PostDetail from './pages/PostDetail'
import PostList from './pages/PostList'
import ProductList from './pages/ProductList'

function App() {
  return (
    <BrowserRouter>
      <nav>
        <Link to="/">記事</Link> | <Link to="/products">商品</Link>
      </nav>
      <Routes>
        <Route path="/" element={<PostList />} />
        <Route path="/posts/:postId" element={<PostDetail />} />
        <Route path="/products" element={<ProductList />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
```

✅ 検証済み: react-router 8.4.0 / TypeScript 7.0.2（`npm run build`・`npm run lint` も通過）

`npm run dev` で `http://localhost:5173/` を開くと、記事が新しい順に並びます（`scripts/seed.py` の15件と、手で入れた記事）。

```text
記事 | 商品
記事一覧（19件）
・旅の持ち物リスト（旅行）
・北海道でキャンプ（旅行）
…
```

タイトルをクリックすると、`/posts/<id>` に移って詳細が出ます。

```text
記事 | 商品
← 記事一覧へ
Django のモデル入門
プログラミング / 2026/11/1 8:58:15
#python #django
ForeignKey と ManyToManyField の違いをまとめた。
```

✅ 検証済み: Chromium（Playwright）で、一覧 → クリック → 詳細、上の「商品」で商品一覧に移ることを確認（件数・id・日時は環境で変わる）

**④ 壊れるのを見る**

無い記事の URL、`http://localhost:5173/posts/9999` を直接開きます。

画面が**真っ白**になります。上の「記事 | 商品」まで消えます。Console には、次のエラーが出ます。

```text
Failed to load resource: the server responded with a status of 404 (Not Found)
TypeError: Cannot read properties of undefined (reading 'map')
    at PostDetail (http://localhost:5173/src/pages/PostDetail.tsx:...)
```

✅ 検証済み: Chromium で確認

Django は正しく 404 を返しています。

```bash
curl -s http://127.0.0.1:8000/api/posts/9999
```

```text
{"detail": "Not Found: No Post matches the given query."}
```

✅ 検証済み: Django 5.2.17 / django-ninja 1.7.1（ステータスは 404）

なのに、`fetch` は **404 でも失敗にしません**。`getJson` はこの `{"detail": ...}` を `Post` として返し、`post.tags.map(...)` で `tags` が無くて落ちました。型は「`Post` のはず」と言っているだけで、中身を確かめてはいません。

**⑤ 直す**

`frontend/src/api/client.ts` の `getJson` の、`const res = ...` の下に4行

```ts
  if (!res.ok) {
    // fetch は 404 や 500 では例外にしない。2xx 以外は、ここで例外にする
    throw new Error(`${res.status} ${res.statusText}`)
  }
```

✅ 検証済み: `npm run build`・`npm run lint` が通る

もう一度 `/posts/9999` を開くと、こうなります。

```text
記事 | 商品
読み込めませんでした: Error: 404 Not Found
```

✅ 検証済み: Chromium で確認

直したのは `client.ts` の1か所だけですが、3つの画面が全部 `getJson` を使っているので、どの画面も 404 や 500 で真っ白にならなくなりました。

コミットするときは、`npm install` で変わった `package.json`・`package-lock.json` と、`src/` の新しいファイル（`api/client.ts`・`pages/`）も一緒に入れます。

### 3-2. 🔬 仕組み解剖

| | React Router（`BrowserRouter` / `Routes` / `Route` / `Link` / `useParams`） |
| --- | --- |
| 正式名称 | React Router の「宣言型」（declarative mode）の使い方。`<Route path="..." element={...} />` を並べて書く |
| いつ・誰が | URL が変わるたびに、`Routes` が `Route` を上から見て、合う `element` を出す。`/posts/:postId` の `:postId` の部分は、`useParams()` で文字列として取れる |
| 発行される SQL | 画面の切り替え自体では無し。詳細を開くたびに `GET /api/posts/<id>` が1本飛び、Django 側で SQL が走る |
| TS での対応物 | これ自体が TS / React 側の道具。Django の `urls.py`（URL → ビュー）を、画面の側でやっているもの |
| なぜこの設計 | `<Link>` はページを読み込み直さないので、速く、画面の状態も消えない。URL は残るので、詳細の URL を共有・再読み込みもできる |
| 失敗すると | 合う `Route` が無い URL（`/nope`）では何も出ず、Console に `No routes matched location "/nope"` と警告が出る |

✅ 検証済み: react-router 8.4.0（`<Link>` で移る前に `window` に置いた値が、移った後も残っている = ページは読み込み直されていない）
根拠: https://reactrouter.com/start/declarative/routing

```text
  /                 → <PostList />     → GET /api/posts       → {"items": [...], "count": 19}
  /posts/1          → <PostDetail />   → GET /api/posts/1     → 200 {"id": 1, ...}
  /posts/9999       → <PostDetail />   → GET /api/posts/9999  → 404 {"detail": ...}
                                            getJson が throw → 「読み込めませんでした」
  /products         → <ProductList />  → GET /api/products
```

✅ 検証済み: ③〜⑤

**`fetch` が失敗にするのは「届かなかった」ときだけ**

`fetch` の Promise が失敗（reject）になるのは、URL の誤りやネットワークの切断など、**応答が返ってこなかった**ときだけです。404 や 500 でも、応答が返ってくれば成功（resolve）です。だから、`res.ok`（ステータスが 200〜299 なら `true`）を自分で確かめます。
根拠: https://developer.mozilla.org/en-US/docs/Web/API/Window/fetch

4-1 の CORS で出た `Failed to fetch` は、応答が**ブラウザに捨てられた**ので「届かなかった」扱いになり、`.catch` に来ていました。今回の 404 とは違う種類の失敗です。

### 3-3. 🐍 Python注

新しい文法はありません。

TypeScript の側で1つだけ補足します。

- `getJson<T>(path)` の `<T>` は、**型の引数**（ジェネリクス）。呼ぶ側が `getJson<Post>(...)` と型を渡すと、戻り値が `Promise<Post>` になる。Python の `def get_json[T](path: str) -> T:` と同じ考え方
- ただし `as T` は「そういうことにする」という宣言で、中身は確かめない。④が壊れたのはこのため

### 3-4. 解説 — なぜこう設計するか

API を呼ぶ処理を `client.ts` にまとめたのは、⑤のように**全部の画面に効く直しを、1か所で済ませる**ためです。4-4 では、ここに「ログインの身分証（JWT）を `Authorization` ヘッダに付ける」処理を足します。画面ごとに書いていたら、全部の画面を直すことになります。

画面の側は、`error`・読み込み中（`null`）・中身ありの3つの状態を、上から順に `return` で出し分けています。Django の 404 は「そんな記事は無い」という正しい答えなので、画面もそれを伝えられるようにしておきます。

🧠 Django の考え方: Django は、無いものには 404、形の違う入力には 422 と、**ステータスで答えを分ける**（1-9・1-7）。画面の側も、ステータスを見てから中身を読む。

### 3-5. ⚠️ アンチパターン ／ 🔓 教材用の簡略化

> ⚠️ **アンチパターン**: `fetch(...).then((res) => res.json())` のように、`res.ok` を見ずに JSON を読む。404 や 500 の中身（`{"detail": ...}`）を、正しいデータとして使ってしまう（④）。
> 根拠: https://developer.mozilla.org/en-US/docs/Web/API/Response/ok

> 🔓 **教材用の簡略化**: エラーは `Error: 404 Not Found` と、ステータスをそのまま画面に出している。
> **本番では**: 404 なら「記事が見つかりません」、ネットワークの失敗なら「通信できませんでした」のように、利用者向けの言葉に変える。Django が返す `detail` も、画面に出すかは選ぶ（中身が開発者向けのことがある）。

> 🔓 **教材用の簡略化**: `/posts/3` を直接開いたり再読み込みしたりしても動くのは、Vite の開発サーバが、どの URL にも `index.html` を返しているから。
> **本番では**: 画面を配るサーバ（nginx など）にも、「無いパスには `index.html` を返す」設定が要る。無いと、詳細の URL を再読み込みしたときに 404 になる。
> 根拠: https://vite.dev/guide/static-deploy

### 3-6. 🔮 予測 → 動作確認

1. `http://localhost:5173/nope`（どの `Route` にも合わない URL）を開いたら？
2. `http://localhost:5173/posts/abc` を開いたら？ Django は何を返す？
3. 記事の詳細を開いたまま、ブラウザで再読み込み（⌘R）したら？

<details><summary>答え</summary>

1. 上の「記事 | 商品」だけが出て、下は空。Console に `No routes matched location "/nope"` の警告（`StrictMode` なので2回）。エラーではないので、真っ白にはならない（検証済み）。直すなら、`Routes` の最後に `<Route path="*" element={<p>ページが見つかりません</p>} />` を足す（`*` はどの URL にも合う。検証済み: `/nope` で「ページが見つかりません」が出る）
2. 「読み込めませんでした: Error: 422 Unprocessable Content」。`post_id: int` に `abc` は入らないので、Ninja が 422 を返す（1-7）。React Router は `:postId` を文字列のまま渡すだけで、数字かどうかは確かめていない（検証済み）
3. 同じ詳細がもう一度出る。Vite の開発サーバが `/posts/1` にも `index.html` を返し、React Router が URL を見て `PostDetail` を出すから（検証済み: `/posts/3` も `index.html` で 200）。本番では 3-5 の設定が要る

</details>

### 3-7. ✅ 想起チェック

1. `fetch` は、404 が返ってきたとき失敗（reject）になる？
2. `/posts/:postId` の `postId` は、画面の中でどうやって取る？ 型は？

<details><summary>答え</summary>

1. ならない。応答が返ってくれば成功。`res.ok` を自分で確かめる
2. `useParams()` で取る。型は文字列（`string | undefined`）。数字に変えていないので、Django 側の `int` の検証（422）が最後の砦になる

</details>

### 3-8. 📇 まとめカード

この回で覚えることは1つだけ: **`fetch` は 404 でも失敗にしない。API を呼ぶ処理を1か所にまとめ、そこで `res.ok` を確かめる。**

📒 用語集に追記: React Router / `useParams` / `res.ok` / ジェネリクス

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第4部 ステップ4` — ログイン画面


---

## 第4部-4: ログイン画面

**❓ この回の問い**: 2-6 で、ログインすると身分証（access、5分）と引換券（refresh、1日）が返るようにした。画面からログインして、注文履歴のような「本人だけが見られる API」を呼ぶ。5分たって身分証が切れたら、利用者にもう一度パスワードを打たせる？

**作るもの**: ログイン画面と注文履歴の画面。身分証が切れたら、引換券で新しい身分証をもらい、自動でやり直す
**重要度**: 🔴 毎日使う — JWT を使う画面なら、必ずこの「切れたら更新」を書く
**前ステップとの接続**: 2-6 の `/auth/login`・`/auth/refresh`、3-9 の `GET /api/orders` を画面から呼ぶ。4-3 の `client.ts` に足す。4-1 の「⏭️ プリフライト」をここで回収する

### 4-0. このステップの初出

**Django / Ninja**: なし（2-6 の JWT を使い回す） / **Python**: なし

> 🧒 **かみくだくと**: **localStorage** は、ブラウザがサイト（オリジン）ごとに持つ、小さな保存場所。ページを閉じても残る。ここに身分証と引換券を入れておく。

### 4-1. 実践

✋ **コピペで構いません。** ただし打ち終わったら、**どこか1行だけ変えて**動かしてください。
変数名でも、文字列でも、数字でもいい。それだけで「読む」が「判断する」に変わります。

**① `client.ts` に、ログインと「身分証付きの GET」を足す**

`frontend/src/api/client.ts` の先頭に追加

```ts
import type { components } from './schema'

type TokenOut = components['schemas']['TokenOut']
```

ファイルの最後に追加

```ts
// ログインして、身分証（access）と引換券（refresh）をブラウザに保存する
export async function login(username: string, password: string): Promise<void> {
  const res = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}`)
  }
  const tokens = (await res.json()) as TokenOut
  localStorage.setItem('access', tokens.access)
  localStorage.setItem('refresh', tokens.refresh)
}

// ログアウト。保存した身分証と引換券を消す
export function logout(): void {
  localStorage.removeItem('access')
  localStorage.removeItem('refresh')
}

// 身分証を Authorization ヘッダに付けて GET する
function fetchWithAccess(path: string): Promise<Response> {
  return fetch(`${API_URL}${path}`, {
    headers: { Authorization: `Bearer ${localStorage.getItem('access')}` },
  })
}

// ログインが要る API を GET して、返ってきた JSON を T 型として返す
export async function getJsonWithAuth<T>(path: string): Promise<T> {
  const res = await fetchWithAccess(path)
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}`)
  }
  return (await res.json()) as T
}
```

`TokenOut` は、4-2 で作った `schema.d.ts` にある、Django の `TokenOut`（`access` と `refresh`）の型です。

**② 画面を2つ足す**

`frontend/src/pages/Login.tsx` を新規作成

```tsx
import { useState } from 'react'
import type { SubmitEvent } from 'react'
import { useNavigate } from 'react-router'
import { login } from '../api/client'

function Login() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  function handleSubmit(e: SubmitEvent<HTMLFormElement>) {
    e.preventDefault() // フォームの既定の送信（ページの読み込み直し）を止める
    login(username, password)
      .then(() => navigate('/orders')) // ログインできたら注文履歴へ
      .catch((e: unknown) => setError(String(e)))
  }

  return (
    <main>
      <h1>ログイン</h1>
      {error && <p>ログインできませんでした: {error}</p>}
      <form onSubmit={handleSubmit}>
        <p>
          <label>
            ユーザー名 <input value={username} onChange={(e) => setUsername(e.target.value)} />
          </label>
        </p>
        <p>
          <label>
            パスワード{' '}
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
        </p>
        <button type="submit">ログイン</button>
      </form>
    </main>
  )
}

export default Login
```

`frontend/src/pages/OrderList.tsx` を新規作成

```tsx
import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { getJsonWithAuth, logout } from '../api/client'
import type { components } from '../api/schema'

type Order = components['schemas']['OrderOut']

// 注文の状態の、画面に出す名前。Status の3つのどれかが抜けると、型のエラーになる
const STATUS_LABEL: Record<components['schemas']['Status'], string> = {
  placed: '確定',
  shipped: '発送済み',
  completed: '完了',
}

function OrderList() {
  const navigate = useNavigate()
  const [orders, setOrders] = useState<Order[] | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getJsonWithAuth<Order[]>('/orders')
      .then((data) => setOrders(data))
      .catch((e: unknown) => setError(String(e)))
  }, [])

  function handleLogout() {
    logout()
    navigate('/login')
  }

  if (error) {
    return (
      <main>
        <p>読み込めませんでした: {error}</p>
        <p>
          <Link to="/login">ログインする</Link>
        </p>
      </main>
    )
  }
  if (orders === null) return <p>読み込み中…</p>

  return (
    <main>
      <h1>注文履歴</h1>
      <button onClick={handleLogout}>ログアウト</button>
      <ul>
        {orders.map((order) => (
          <li key={order.id}>
            注文 {order.id}（{STATUS_LABEL[order.status]}）— 合計 {order.total} 円
            <ul>
              {order.items.map((item) => (
                <li key={item.product_id}>
                  {item.name} × {item.quantity}
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ul>
    </main>
  )
}

export default OrderList
```

`frontend/src/App.tsx` を、全文置き換える

```tsx
import { BrowserRouter, Link, Route, Routes } from 'react-router'
import Login from './pages/Login'
import OrderList from './pages/OrderList'
import PostDetail from './pages/PostDetail'
import PostList from './pages/PostList'
import ProductList from './pages/ProductList'

function App() {
  return (
    <BrowserRouter>
      <nav>
        <Link to="/">記事</Link> | <Link to="/products">商品</Link> |{' '}
        <Link to="/orders">注文履歴</Link> | <Link to="/login">ログイン</Link>
      </nav>
      <Routes>
        <Route path="/" element={<PostList />} />
        <Route path="/posts/:postId" element={<PostDetail />} />
        <Route path="/products" element={<ProductList />} />
        <Route path="/orders" element={<OrderList />} />
        <Route path="/login" element={<Login />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
```

✅ 検証済み: react-router 8.4.0 / TypeScript 7.0.2 / @types/react 19.3.0（`npm run build`・`npm run lint` も通過）

`FormEvent` ではなく `SubmitEvent` を使っています。今の React の型では、`FormEvent` は「実在しない」として非推奨（`@deprecated`）になっているためです。

**③ ログインしてみる**

「ログイン」を開き、`scripts/seed.py` で作った carol（パスワード `pass1234`）で入ります。注文履歴に移って、carol の注文が新しい順に出ます。

```text
記事 | 商品 | 注文履歴 | ログイン
注文履歴
[ログアウト]
・注文 3（確定）— 合計 7180.00 円
    ・USB-C 充電器 65W × 1
    ・SQL 図鑑 × 1
・注文 2（発送済み）— 合計 1650.00 円
    ・ステンレスマグカップ × 1
・注文 1（完了）— 合計 4036.00 円
    ・Django 入門 × 1
    ・冒険マンガ 1巻 × 2
```

✅ 検証済み: Chromium（Playwright）で表示（注文の id は環境で変わる）。パスワードを間違えると「ログインできませんでした: Error: 401 Unauthorized」

Django のログを見ると、4-1 で予告した**プリフライト**が出ています。

```text
"OPTIONS /api/auth/login HTTP/1.1" 200 0
"POST /api/auth/login HTTP/1.1" 200 486
"OPTIONS /api/orders HTTP/1.1" 200 0
"OPTIONS /api/orders HTTP/1.1" 200 0
"GET /api/orders HTTP/1.1" 200 808
"GET /api/orders HTTP/1.1" 200 808
```

✅ 検証済み: runserver のログ（2本ずつなのは `StrictMode` のため。4-1 の🔮）

ログインの POST は `Content-Type: application/json`、注文履歴の GET は `Authorization` ヘッダ付きです。どちらも「そのまま送ってよい簡単な呼び出し」に入らないので、ブラウザが先に `OPTIONS` で尋ねています。4-1 で入れた django-cors-headers が、これに 200 で答えています。

**④ 壊れるのを見る**

ログインしたまま **5分待って**、注文履歴を再読み込みします（待つ代わりに、開発者ツールの「Application」→「Local Storage」で `access` の値を1文字書き換えても、同じことが起きます）。

```text
読み込めませんでした: Error: 401 Unauthorized
ログインする
```

✅ 検証済み: スクラッチだけ身分証の期限を20秒に縮め、期限切れで 401 になるのを確認（教材のアプリの設定は変えていない）

引換券はまだ1日有効なのに、身分証が切れただけで、利用者は追い出されました。5分ごとにパスワードを打たせるのは、使い物になりません。

**⑤ 直す: 切れたら、引換券で取り替えて1回だけやり直す**

`client.ts` の `type TokenOut = ...` の下に1行

```ts
type AccessOut = components['schemas']['AccessOut']
```

`// ログインが要る API を GET して ...` の関数の、**すぐ上**に追加

```ts
// 引換券で、新しい身分証をもらう。引換券が無いか切れていたら、ログアウトして false
async function refreshAccess(): Promise<boolean> {
  const refresh = localStorage.getItem('refresh')
  if (refresh === null) {
    return false
  }
  const res = await fetch(`${API_URL}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  })
  if (!res.ok) {
    logout()
    return false
  }
  const data = (await res.json()) as AccessOut
  localStorage.setItem('access', data.access)
  return true
}
```

`getJsonWithAuth` を、次のものに置き換える

```ts
// ログインが要る API を GET して、返ってきた JSON を T 型として返す
export async function getJsonWithAuth<T>(path: string): Promise<T> {
  let res = await fetchWithAccess(path)
  if (res.status === 401 && (await refreshAccess())) {
    // 身分証が切れていた。新しい身分証で、1回だけやり直す
    res = await fetchWithAccess(path)
  }
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}`)
  }
  return (await res.json()) as T
}
```

✅ 検証済み: `npm run build`・`npm run lint` が通る

もう一度④と同じことをすると、今度は注文履歴がそのまま出ます。Django のログでは、こう流れています。

```text
"GET /api/orders HTTP/1.1" 401 427
"OPTIONS /api/auth/refresh HTTP/1.1" 200 0
"POST /api/auth/refresh HTTP/1.1" 200 242
"GET /api/orders HTTP/1.1" 200 808
```

✅ 検証済み: 期限切れ・`access` の書き換えのどちらでも、401 → refresh → やり直しで 200（`StrictMode` で各2本出る。上は1本ずつに省略）

コミットするときは、`src/api/client.ts` と、新しい `pages/Login.tsx`・`pages/OrderList.tsx`、`App.tsx` を入れます。

### 4-2. 🔬 仕組み解剖

| | 身分証の自動更新（`getJsonWithAuth` + `refreshAccess`） |
| --- | --- |
| 正式名称 | 対応する Django / Ninja の機能は無い。2-6 の `/auth/refresh`（`RefreshToken(...).access_token`）を、画面の側から呼ぶ仕組み |
| いつ・誰が | `getJsonWithAuth` が 401 を受け取ったときだけ、`refreshAccess` が `POST /auth/refresh` を呼ぶ。新しい身分証を保存して、元の GET を1回だけやり直す |
| 発行される SQL | `/auth/refresh` 自体は SQL を出さない（引換券の署名と期限を確かめるだけ）。やり直した `GET /api/orders` は、`JWTAuth` が身分証の持ち主を引く1本と、3-9 の2本で、計3本 |
| TS での対応物 | axios の interceptor（応答を横取りする仕組み）で書くのが定番。ここでは `fetch` で同じことを手で書いた |
| なぜこの設計 | 身分証は短く（盗まれても5分で使えなくなる）、引換券は長く（利用者は1日ログインし直さなくてよい）。この2つを両立させるのが「切れたら交換」 |
| 失敗すると | 引換券も切れていたら（1日たった・書き換えられた）、`/auth/refresh` も 401。`logout()` で両方消し、「ログインする」を出す |

✅ 検証済み: django-ninja-jwt の既定（`ROTATE_REFRESH_TOKENS` は `False`。引換券は交換しても変わらない）
✅ 検証済み: SQL のログで、`/auth/refresh` は0本、`GET /api/orders` は3本
根拠: https://eadwincode.github.io/django-ninja-jwt/settings/

```text
  OrderList → getJsonWithAuth('/orders')
                │  GET /api/orders  Authorization: Bearer <access>
                ├─ 200 → そのまま返す
                └─ 401（身分証が切れた）
                     └─ refreshAccess()  POST /api/auth/refresh {"refresh": ...}
                          ├─ 200 → 新しい access を保存 → GET /api/orders をもう1回 → 200
                          └─ 401（引換券も切れた）→ logout() → 401 のまま投げる → 「ログインする」
```

✅ 検証済み: ⑤と、引換券を書き換えて `/auth/refresh` が 401 → 保存場所が空になるのを確認

**ブラウザの「下見」（プリフライト）が飛ぶ条件**

ブラウザは、別のオリジンへの呼び出しのうち、`GET`・`POST` などで、ヘッダも `Content-Type` も「フォーム送信と同じくらい」のものだけを、そのまま送ります。`Authorization` を付けたり、`Content-Type: application/json` にしたりすると、先に `OPTIONS` で尋ねます。答え（`access-control-max-age: 86400`、4-1）はしばらく覚えるので、毎回は飛びません。2回目のログインでは `OPTIONS` が出ませんでした。
根拠: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS#preflighted_requests

### 4-3. 🐍 Python注

新しい文法はありません。

TypeScript の側で1つだけ補足します。`Record<Status, string>` は「`Status` の値（`placed`・`shipped`・`completed`）を全部キーに持つ辞書」の型です。Python の `dict[str, str]` と違い、キーが1つでも欠けるとビルドが止まります（🔮1）。

### 4-4. 解説 — なぜこう設計するか

ログインが要る呼び出しを `getJsonWithAuth` の1か所にしたので、更新の仕組みも1か所に書けば済みました。注文履歴の画面（`OrderList`）は、身分証が切れたことを知りません。4-5 で注文を確定する POST を足すときも、同じ形で包めば、更新は自動で効きます。

やり直しを「1回だけ」にしているのは、更新に失敗し続けたときに、無限に呼び続けないためです。

🧠 Django の考え方: Django の側は、身分証の中身（署名と期限）だけを見て、通すか 401 かを決める。「切れたら更新」は、利用者の手元（画面）の責任。サーバは、ログイン中の人の状態を覚えていない。

### 4-5. ⚠️ アンチパターン ／ 🔓 教材用の簡略化

> ⚠️ **アンチパターン**: 401 が来たら、すぐログイン画面に飛ばす。引換券がまだ使えるのに、利用者に5分ごとにパスワードを打たせることになる（④）。

> 🔓 **教材用の簡略化**: 身分証と引換券を `localStorage` に入れている。
> **本番では**: `localStorage` は、そのページで動く JavaScript なら何でも読める。悪いスクリプトが入り込む（XSS）と、引換券ごと盗まれる。OWASP は、ログインの状態を表す値を `localStorage` に入れないよう勧めている。本番では、引換券を JavaScript から読めない Cookie（`HttpOnly`）に入れ、身分証はメモリだけに持つ、などの形にする。
> 根拠: https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html#local-storage

> 🔓 **教材用の簡略化**: ナビの「ログイン」は、ログイン中も出たまま。ログイン中かどうかを画面全体で共有していない。
> **本番では**: ログイン中のユーザーを React の Context などで共有し、ナビの表示を切り替える。

### 4-6. 🔮 予測 → 動作確認

1. `OrderList.tsx` の `STATUS_LABEL` から `completed: '完了',` の行を消したら？
2. ログアウトした状態（保存場所が空）で、注文履歴を開いたら？ `/auth/refresh` は呼ばれる？
3. ⑤のあと、身分証が切れた状態で注文履歴を開くと、`POST /auth/refresh` は何回飛ぶ？

<details><summary>答え</summary>

1. `npm run build` が止まる。`error TS2741: Property 'completed' is missing in type '{ placed: string; shipped: string; }' but required in type 'Record<"completed" | "placed" | "shipped", string>'.`（検証済み）。Django に状態を足して `npm run gen:api` を流すと、ここで「名前を付け忘れている」と教えてくれる
2. 「読み込めませんでした: Error: 401 Unauthorized」。`/auth/refresh` は呼ばれない。引換券が無い（`null`）ので、`refreshAccess` は送る前に `false` を返す（検証済み: ログは `GET /api/orders` の 401 だけ）
3. 2回。`StrictMode` で effect が2回走り、2つの `getJsonWithAuth` がそれぞれ 401 を受けて、それぞれ更新するから（検証済み）。今は引換券が交換で変わらない設定（`ROTATE_REFRESH_TOKENS = False`）なので、2回とも成功する。交換のたびに引換券を変える設定にすると、先に終わった方が古い引換券を無効にし、後の方が失敗することがある。本番では、更新中の Promise を1つにまとめる

</details>

### 4-7. ✅ 想起チェック

1. 身分証（access）と引換券（refresh）、有効期限が長いのはどっち？ なぜ長さを変える？
2. 401 が返ってきたとき、`getJsonWithAuth` は何をする？

<details><summary>答え</summary>

1. 引換券（1日）。身分証は毎回送るので盗まれやすく、短くしておく（5分）。引換券は更新のときだけ送るので長くでき、利用者は1日ログインし直さなくてよい
2. 引換券で新しい身分証をもらい、保存して、同じ GET を1回だけやり直す。引換券も切れていたら、両方消して 401 のまま投げる

</details>

### 4-8. 📇 まとめカード

この回で覚えることは1つだけ: **401 が来たら、すぐ追い出さずに、引換券（refresh）で身分証（access）を取り替えて1回だけやり直す。それも失敗したら、ログインし直してもらう。**

📒 用語集に追記: localStorage / 身分証の自動更新 / `Record<K, V>`

---
❓ 分からない言葉があれば `?: <言葉>` と送ってください。
   そこだけ説明して、`docs/_glossary.md` に追記します。

▶ **次**: `M1: 第4部 ステップ5` — カートと注文画面
