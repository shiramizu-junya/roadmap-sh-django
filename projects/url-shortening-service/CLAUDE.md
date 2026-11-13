# CLAUDE.md — URL Shortening Service

AI（Claude Code）がこのフォルダで作業するときのルール。

## 1. このアプリは何か

- roadmap.sh の課題「URL Shortening Service」を、**本編とは独立した Django アプリ**として作る
- 何を作るかは `docs/requirements.md` に書いてある。**要件の正はこのファイルだけ**
- 今の範囲は `POST /shorten` だけ。ほかのエンドポイントは作らない

## 2. 技術スタック

| 種類 | 使うもの |
|---|---|
| 言語 | Python 3.14 |
| フレームワーク | Django 5.2 / Django Ninja 1.7（Pydantic 2） |
| DB | MySQL 8.4（本編の Docker コンテナを共有。データベース名は `shortener`） |
| テスト | pytest / pytest-django / Ninja の `TestClient` |
| 道具 | uv / ruff / mypy + django-stubs |

- 仮想環境（`.venv`）はリポジトリ直下のものを共有する。**新しいライブラリは勝手に追加しない**（必要なら理由を添えて人間に聞く）
- 設定は**このフォルダ専用の `.env`** から読む（`DB_NAME=shortener`）。リポジトリ直下の本編の `.env` は読まない・使わない
  - 本編の学習用データベース（`blog`）を誤って使わないため。設定ファイルに書いてあるとおりのデータベースを使う形にする
  - コミットするのは値の入っていない `.env.example` だけ。`.env` は Git の対象外（確認済み）
- タイムゾーンは `TIME_ZONE = "UTC"`

## 3. 置き場所

```
projects/url-shortening-service/
├── CLAUDE.md          このファイル
├── docs/              要件・設計（人間が書く）
├── manage.py
├── pytest.ini         このフォルダ専用の pytest 設定
├── shortener_project/ 設定（settings.py / urls.py）
└── shortener/         アプリ本体（models.py / api.py / tests/）
```

- 設定パッケージ名を `config` にしない（本編の `config` と名前がぶつかるため）

## 4. コマンド

**すべてこのフォルダ（`projects/url-shortening-service/`）で実行する。**

```sh
uv run python manage.py runserver 8001   # 本編（8000）と同時に動かせるよう 8001
uv run python manage.py makemigrations
uv run python manage.py migrate
uv run pytest                            # このフォルダの pytest.ini を使う
uv run ruff check . && uv run ruff format --check .
uv run mypy .
```

## 5. やってはいけないこと

- **このフォルダの外のファイルを変更しない**（本編の `blog/`・`shop/`・`config/`、リポジトリ直下の `pyproject.toml` など）
- **MySQL の設定（データベースの作成、権限の付与など）を自分で実行しない**。実行するコマンドを書いて人間に渡し、人間が実行する
- **要件に無い機能を足さない**（短縮コードの指定、リダイレクト、一覧、認証など）
- **要件に書いてあることを、出典（roadmap.sh）の例に合わせて変えない**（例: `id` は数値。出典の例は文字列だが従わない）
- **曖昧なところを推測で埋めない**。要件で決まっていないことに当たったら、実装を止めて人間に質問する
- テストを通すために、テストや要件の方を書き換えない

## 6. 進め方

1. `docs/tasks.md` のタスクを**1つだけ**やる（tasks.md が無いうちは、人間に指示されたことだけをやる）
2. 受け入れ条件をテストに書く → 実装する → テストを通す
3. 終わったら、何を変えたか・どの受け入れ条件を満たしたか・迷ったところを短く報告する

## 7. 完了の定義

次がすべて満たされたら完了。1つでも満たせなければ、完了と報告しない。

- [ ] `uv run pytest` が全部通る
- [ ] `uv run ruff check .` と `uv run mypy .` でエラーが無い
- [ ] `docs/requirements.md` の受け入れ条件それぞれに、対応するテストがある
- [ ] このフォルダの外のファイルを変更していない
