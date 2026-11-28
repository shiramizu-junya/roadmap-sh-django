# 拡張モジュール

本編が終わったあと、必要になったものだけ足す。`MX: <name>` で呼ぶ。

| name | 内容 | 前提 | 新しく必要なもの | 目安 |
|---|---|---|---|---|
| `celery` | 非同期処理（画像リサイズ・一括メール） | 第3部まで | Redis コンテナ | 3〜4 |
| `websocket` | リアルタイム通知 | 第3部まで | Django Channels / Redis | 3〜4 |
| `search` | 全文検索 | 第2部まで | Elasticsearch コンテナ | 3〜4 |
| `cache` | キャッシュ機構 | 第2部まで | Redis コンテナ | 2〜3 |
| `signals` | シグナル（と使いすぎの危うさ） | 第2部まで | なし | 1〜2 |
| `drf` | DRF なら同じ API をどう書くか（比較のみ） | 第2部まで | djangorestframework | 1〜2 |
| `basic-auth` | Basic 認証（毎回、名前と合言葉を送る）。なぜ使われなくなったか | 第2部まで | なし | 1〜2 |
| `session-auth` | セッション認証（Cookie で入場券を持たせる）。CSRF の検査を戻す | `basic-auth` | なし（Django 標準の sessions） | 2〜3 |
| `oauth` | OAuth 2.0（合言葉を渡さずに「許可」だけ渡す）。最後の1ステップで OpenID Connect | `session-auth` | Keycloak コンテナ | 3〜4 |
| `web-security` | ハッシュ（bcrypt など）・HTTPS と SSL/TLS・CORS・CSP・OWASP・サーバーの守り。`MX: web-security 1` のように分けて呼ぶ | `oauth` | なし | 5〜6 |

**認証の3つは、上から順に呼ぶ。** 前のやり方で困ったことを、次のやり方が解決する順になっている。Token 認証・JWT は第2部（2-6）で済んでいる。認証のあとは `web-security`、その次に `cache`。

**本編のあとは、roadmap.sh/backend を上から順に進める**（`docs/_prompt.md` §2.7）。次は `MX: basic-auth`。
SAML・GraphQL・gRPC・SOAP は、ロードマップで「いつ学んでもよい」の印なので、今は入れない。

**あとから足したくなったら、この表に行を追加する。**
（多言語対応などは今回入れていないが、必要になれば追加できる）
