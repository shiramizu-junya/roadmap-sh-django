# テンプレート・Static・Media 完全入門

> **このドキュメントの読み方**
> 上から順に読み、コードブロックを **自分の手で** プロジェクトに書き写しながら進めてください。各章末の「ハンズオン」が、その章の知識を使って既存の `polls/` アプリを一段ずつ作り込んでいきます。完走すると polls が「CSS が当たった見た目つき・質問のカバー画像をアップロードできる・カスタムテンプレートタグで集計表示する」アプリに育ちます。
>
> **前提**: `docs/01-manage-py-and-urls.md` と `docs/02-models-views-tests-admin-migrations.md` を完了している状態。`polls/` のビューが ORM ベースに書き換わっていて、テンプレートが既に `polls/templates/polls/{index,detail,results}.html` に存在する — のところからスタートします。

---

## このドキュメントで作るもの

完走後の polls の状態：

| 項目 | できるようになること |
|---|---|
| 共通レイアウト | `base.html` を継承して各ページの見た目が統一される |
| CSS | `polls/static/polls/style.css` で見た目を整える |
| カバー画像 | `Question.cover_image` をアップロード、一覧と詳細ページで表示 |
| 部品化 | `_question_item.html` を `{% include %}` で再利用 |
| カスタムタグ | `polls_tags.py` の独自フィルタで「投票合計」「上位選択肢」を表示 |
| 本番準備 | `collectstatic` の意味を理解し、ローカルでも一度実行できる |

完走後に身につく知識：
- **テンプレート言語の文法**: 変数 `{{ }}` / タグ `{% %}` / フィルタ `|` / コメント
- **継承と部品化**: `{% extends %}` / `{% block %}` / `{% include %}` の使い分け
- **Static** と **Media** の違い、設定の意味
- `{% load static %}` と `{% static '...' %}`、ネームスペーシングの重要性
- `MEDIA_URL` / `MEDIA_ROOT` / `ImageField` / `FileField` / `Pillow`
- 開発時 (`DEBUG=True`) と本番 (`DEBUG=False`) で配信の仕組みが変わる理由
- `collectstatic` の役割、WhiteNoise / Nginx の選び方
- カスタムテンプレートタグとフィルタの作り方
- コンテキストプロセッサで「全テンプレートから使える変数」を増やす方法

---

# 第1章 テンプレートの仕組みを理解する

## 1-1. テンプレートって何？

Django の **テンプレート** は、HTML に「穴」を空けておき、Python 側から渡したデータでその穴を埋めて最終的な HTML を作るための仕組みです。これは「テンプレートエンジン」と呼ばれる仕掛けで、Django には **DTL（Django Template Language）** と **Jinja2** の2種類が同梱されています。本ドキュメントでは DTL を扱います。

イメージ：

```
テンプレート (HTML + 穴)
       +
コンテキスト (Python の dict)
       │
       ▼
   レンダリング
       │
       ▼
   完成した HTML
```

`polls/views.py:13` で書いた `render(request, "polls/index.html", {"latest_question_list": ...})` がまさにこれをやっています。第2引数のテンプレートに、第3引数の dict を埋め込んで HTML を生成し、HttpResponse として返す——という流れです。

## 1-2. DTL の4種類の構文

DTL に出てくる記号は次の4つだけです：

| 記号 | 名前 | 役割 | 例 |
|---|---|---|---|
| `{{ ... }}` | 変数 (variable) | コンテキストの値を出力 | `{{ question.question_text }}` |
| `{% ... %}` | タグ (tag) | ロジックを実行 | `{% for q in questions %}` |
| `\|filter` | フィルタ (filter) | 変数を加工 | `{{ name\|upper }}` |
| `{# ... #}` | コメント | 出力されない | `{# TODO: 後で消す #}` |

それぞれ詳しく見ていきます。

### 変数 `{{ ... }}`

dict のキー、属性、メソッド呼び出し（引数なしのみ）、リストの index 全部 `.` でアクセスできます：

```django
{{ question }}                {# __str__() の結果 #}
{{ question.question_text }}  {# 属性 #}
{{ question.choices.all }}    {# メソッド呼び出し (引数なし) #}
{{ my_list.0 }}               {# index 0 #}
{{ my_dict.key }}             {# dict のキー #}
```

**注意**: `()` を書く必要はありません。`question.choices.all()` ではなく `question.choices.all` です。引数付きのメソッド呼び出しはテンプレートからは直接できません（フィルタやタグでラップします）。

### タグ `{% ... %}`

「処理」を担当します。代表例：

```django
{# 条件分岐 #}
{% if user.is_authenticated %}
    こんにちは {{ user.username }}
{% else %}
    ログインしてください
{% endif %}

{# ループ #}
{% for q in questions %}
    {{ q.question_text }}
{% empty %}
    質問がありません。
{% endfor %}

{# URL 生成 (urls.py の name= を逆引き) #}
<a href="{% url 'polls:detail' question.id %}">詳細</a>

{# CSRF トークン (form 内で必須) #}
{% csrf_token %}
```

`{% empty %}` は「ループ対象が空のときだけ実行されるブロック」です。`for/else` ではなく `for/empty` であることに注意。

### フィルタ `|`

変数の値を出力直前に加工する仕組みです：

```django
{{ "django"|title }}              {# "Django" #}
{{ "hello"|upper }}               {# "HELLO" #}
{{ items|length }}                {# 個数 #}
{{ pub_date|date:"Y-m-d H:i" }}   {# "2026-05-15 14:30" #}
{{ comment|truncatechars:30 }}    {# 30文字で切って "..." #}
{{ html_string|safe }}            {# HTMLエスケープを止める #}
{{ value|default:"未設定" }}       {# 空のとき置き換える #}
```

`|filter:argument` で引数を1つ渡せます。複数のフィルタはチェーンできます：

```django
{{ article.title|lower|truncatechars:20 }}
```

よく使うフィルタの一覧は第7章で扱います。

### コメント `{# ... #}` と `{% comment %}`

```django
{# 1行コメント #}

{% comment %}
複数行のコメント。
レンダリング結果には出ない。
{% endcomment %}
```

HTML コメント `<!-- ... -->` は **クライアントに送られる** ので、ソースを見られても困らないものに限ります。DTL コメントはサーバー側で消えるので、開発メモはこちらを使います。

## 1-3. テンプレートはどこから探される？

Django がテンプレートを探す経路は `config/settings.py:70-83` の `TEMPLATES` 設定で決まります：

```python
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],                # ← プロジェクト共通の探索先（複数可）
        "APP_DIRS": True,          # ← 各アプリの templates/ も探す
        "OPTIONS": { ... },
    },
]
```

| 設定 | 役割 |
|---|---|
| `DIRS` | プロジェクト直下などの「アプリに属さない」テンプレートを探す先のリスト |
| `APP_DIRS` | `True` だと、`INSTALLED_APPS` に登録された全アプリの `<app>/templates/` を自動で探索 |

**探索順序**: まず `DIRS` を上から順に → 次に `INSTALLED_APPS` の上から順に各アプリの `templates/` を見る。

### なぜ `polls/templates/polls/index.html` と二重になっている？

`APP_DIRS=True` は **`polls/templates/` を探す** だけで、その中のファイル名そのものを使います。もし `polls/templates/index.html` と `todo/templates/index.html` が両方あったら、どちらが優先されるかは `INSTALLED_APPS` の順序次第になり、事故ります。

これを防ぐために慣習として「アプリ名のフォルダをもう一階層挟む」ようにします：

```
polls/templates/polls/index.html    ← OK
todo/templates/todo/list.html       ← OK
```

これで `render(request, "polls/index.html", ...)` と書けば確実に polls の方が選ばれます。**Static ファイルでも同じ慣習があるので覚えておいてください**（第4章で再登場）。

## 1-4. `render()` の中で起きていること

```python
return render(request, "polls/index.html", {"latest_question_list": latest})
```

これは以下と同じです：

```python
from django.template.loader import get_template
from django.http import HttpResponse

template = get_template("polls/index.html")
html = template.render({"latest_question_list": latest}, request)
return HttpResponse(html)
```

つまり `render()` は「テンプレート読み込み → コンテキストでレンダリング → HttpResponse でラップ」の3つを1行にまとめたショートカットです。

## ハンズオン 1: 既存テンプレートを読み解く

### 確認するファイル

ブラウザで `http://127.0.0.1:8000/polls/` にアクセスして、ソースを表示しながら次のテンプレートと見比べてください：

```django
{# polls/templates/polls/index.html #}
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>Document</title>
</head>
<body>
    <h1>アンケート</h1>
    <ul>
        {% for question in latest_question_list %}
            <li><a href="{% url 'polls:detail' question.id %}">{{ question.question_text }}</a></li>
        {% endfor %}
    </ul>
</body>
</html>
```

問い：
1. `{{ question.question_text }}` はどこのデータか？ → `views.py` の `Question.objects.filter(...)` の結果のオブジェクトの属性
2. `{% url 'polls:detail' question.id %}` は何の URL を生成する？ → `polls/urls.py` で `name="detail"` がついた `path("<int:question_id>/", ...)` を逆引きして `/polls/<id>/` を生成
3. `{% empty %}` がないので、質問が0件のとき何も出ない。これがテストが失敗していた理由（第7章で対応）。

### Django shell で `render_to_string` を試す

`uv run python manage.py shell_plus` で：

```python
from django.template.loader import render_to_string

html = render_to_string(
    "polls/index.html",
    {"latest_question_list": Question.objects.all()[:3]},
)
print(html)
```

これでビューを通さなくてもテンプレートだけ単独でレンダリングできることが分かります。テスト時にも便利な手法です。

---

# 第2章 テンプレート継承で共通レイアウトを抜き出す

## 2-1. 現状の問題

`polls/templates/polls/index.html`、`detail.html`、`results.html` を見比べると、`<!DOCTYPE html>` から `<title>` までと、`<body>` の閉じタグまでが **完全に同じ** です。これは典型的な重複です。共通部分を切り出す仕掛けが **テンプレート継承** です。

## 2-2. `{% block %}` と `{% extends %}`

仕組みは2つだけ：

- **親** (base) テンプレート: 共通レイアウトを書き、可変な部分を `{% block 名前 %}...{% endblock %}` で穴開けする
- **子** テンプレート: 先頭で `{% extends "親のパス" %}` と宣言し、上書きしたい block だけを書き直す

最小例：

**base.html**
```django
<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}デフォルトタイトル{% endblock %}</title>
</head>
<body>
    {% block content %}{% endblock %}
</body>
</html>
```

**child.html**
```django
{% extends "base.html" %}

{% block title %}記事一覧{% endblock %}

{% block content %}
    <h1>記事一覧</h1>
    <ul>...</ul>
{% endblock %}
```

子が `{% block %}` を書かなかった部分は **親のデフォルト** が使われます。`title` の `{% block %}` にはデフォルト文字列を入れておくと、忘れたときも空白にならなくて便利です。

## 2-3. block.super で親の中身を残しつつ追記

```django
{% block content %}
    {{ block.super }}
    <p>追加コンテンツ</p>
{% endblock %}
```

`{{ block.super }}` は「親の同名 block の中身」に展開されます。共通の冒頭メッセージは残したいけど末尾に何か足したい、というときに便利です。

## 2-4. base はどこに置く？

`polls/` 専用なら `polls/templates/polls/base.html`、プロジェクト全体で共有するなら `templates/base.html`（プロジェクト直下）。後者を使うには `TEMPLATES.DIRS` に `BASE_DIR / "templates"` を追加する必要があります。

今回は polls 専用にとどめます。

## ハンズオン 2: polls に base.html を作る

### 1. `polls/templates/polls/base.html` を新規作成

```django
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}polls{% endblock %} | アンケートアプリ</title>
</head>
<body>
    <header>
        <h1><a href="{% url 'polls:index' %}">アンケートアプリ</a></h1>
    </header>

    <main>
        {% block content %}{% endblock %}
    </main>

    <footer>
        <p><small>&copy; 2026 example</small></p>
    </footer>
</body>
</html>
```

### 2. `index.html` を継承形に書き換え

```django
{% extends "polls/base.html" %}

{% block title %}質問一覧{% endblock %}

{% block content %}
    <ul>
        {% for question in latest_question_list %}
            <li><a href="{% url 'polls:detail' question.id %}">{{ question.question_text }}</a></li>
        {% empty %}
            <li>まだ質問はありません。</li>
        {% endfor %}
    </ul>
{% endblock %}
```

ついでに `{% empty %}` ブロックを追加してテストが期待していた「まだ質問はありません。」を表示するようにしました。

### 3. `detail.html` と `results.html` も同じ要領で

`detail.html`:

```django
{% extends "polls/base.html" %}

{% block title %}{{ question.question_text }}{% endblock %}

{% block content %}
    <h2>{{ question.question_text }}</h2>

    {% if error_message %}
        <p class="error"><strong>{{ error_message }}</strong></p>
    {% endif %}

    <form action="{% url 'polls:vote' question.id %}" method="post">
        {% csrf_token %}
        <fieldset>
            <legend><b>選択肢</b></legend>
            {% for choice in question.choices.all %}
                <input type="radio" name="choice" id="choice{{ forloop.counter }}" value="{{ choice.id }}">
                <label for="choice{{ forloop.counter }}">{{ choice.choice_text }}</label><br>
            {% endfor %}
        </fieldset>
        <input type="submit" value="投票">
    </form>
{% endblock %}
```

`results.html`:

```django
{% extends "polls/base.html" %}

{% block title %}{{ question.question_text }} の結果{% endblock %}

{% block content %}
    <h2>{{ question.question_text }} の結果</h2>

    <ul>
        {% for choice in question.choices.all %}
            <li>{{ choice.choice_text }}: {{ choice.votes }} 票</li>
        {% endfor %}
    </ul>

    <p>
        <a href="{% url 'polls:detail' question.id %}">もう一度投票</a> |
        <a href="{% url 'polls:index' %}">一覧に戻る</a>
    </p>
{% endblock %}
```

### 4. 動作確認

ブラウザで `/polls/`、`/polls/1/`、`/polls/1/results/` を開き、3ページとも同じヘッダー/フッターが付いていること、HTML ソースを見ると `<!DOCTYPE html>` が頭にあり閉じタグまで揃っていることを確認してください。

`uv run python manage.py test polls` も実行。前回失敗していた `test_no_questions` と `test_future_question_is_not_displayed` が PASS するはずです。

---

# 第3章 `{% include %}` で部品化する

## 3-1. include の役割

`{% extends %}` が「外側の枠を継承する」のに対し、`{% include %}` は **「他のテンプレートをこの位置にそのまま貼り付ける」** 仕組みです。React の小さな関数コンポーネントに似ています。

```django
{% include "polls/_question_item.html" %}
```

`_` で始まるファイル名は慣習で「部分テンプレート（パーシャル）」を意味し、単独でレンダリングされないことを示します（必須ではなく、ただの慣習）。

## 3-2. with でコンテキストを差し替え

include 先のテンプレートには **現在のコンテキストがそのまま渡る** ので、ループ変数 `question` などはそのまま使えます。明示的に名前を変えたり、独立した値を渡したい場合は `with` を使います：

```django
{% include "polls/_question_item.html" with q=question %}
{% include "polls/_card.html" with title="お知らせ" body=message only %}
```

`only` を付けると **明示的に渡したもの以外は include 先に渡らなく** なります。意図しないコンテキストの混入を防ぎたいときに便利です。

## 3-3. include vs extends の使い分け

| | extends | include |
|---|---|---|
| 関係 | 外側→内側 | 横並びにパーツを並べる |
| 構造 | 親に block を書き、子で上書き | 完全に独立したファイルを貼り付け |
| 例 | レイアウト（ヘッダー、フッター、ナビ含むスケルトン） | 商品カード、コメント1件、サイドバーモジュール |

「外枠を共有」が extends、「中身の部品を共有」が include、と覚えてください。

## ハンズオン 3: 質問1件分のテンプレートを切り出す

### 1. `polls/templates/polls/_question_item.html` を新規作成

```django
{# 1件分の質問を表示する部品テンプレート。{% include %} 専用 #}
<li>
    <a href="{% url 'polls:detail' question.id %}">{{ question.question_text }}</a>
    <small>（{{ question.pub_date|date:"Y-m-d" }} 公開）</small>
</li>
```

### 2. `index.html` で include を使う

```django
{% extends "polls/base.html" %}

{% block title %}質問一覧{% endblock %}

{% block content %}
    <ul>
        {% for question in latest_question_list %}
            {% include "polls/_question_item.html" %}
        {% empty %}
            <li>まだ質問はありません。</li>
        {% endfor %}
    </ul>
{% endblock %}
```

ループの中で `{% include %}` を呼び出すと、ループ変数 `question` がそのまま include 先で使えます。

### 3. 同じ部品を他のページでも使う

たとえば `results.html` の末尾に「他の質問」リストを足す場合、コードを書き写さずに済みます：

```django
{# results.html の末尾に追加してもいい #}
<h3>他の質問</h3>
<ul>
    {% for question in other_questions %}
        {% include "polls/_question_item.html" %}
    {% endfor %}
</ul>
```

（`other_questions` をビューから渡す前提。試したいなら `views.py` の `results()` で `Question.objects.exclude(pk=question_id)[:3]` を渡すように変えてください。）

ブラウザで `/polls/` を再読み込み → リンクの右側に小さく公開日が出ていれば OK。

---

# 第4章 Static Files — CSS / JS / 画像

## 4-1. Static Files って何？

**Static files** は **「コードと一緒にバージョン管理されて、デプロイ時に一緒に配布される、内容が変わらないファイル群」** のこと。具体的には：

- CSS スタイルシート
- JavaScript ファイル
- ロゴ画像、UI 用の小さい画像（SVG, PNG など）
- フォント

ユーザーがアップロードする画像などは「Media」と呼ばれて別物扱いです（第6章）。

## 4-2. 3つの設定: `STATIC_URL` / `STATICFILES_DIRS` / `STATIC_ROOT`

最初に混乱するのがこの3つの違いです：

| 設定 | 役割 | 開発 | 本番 |
|---|---|---|---|
| `STATIC_URL` | **ブラウザがアクセスする URL のプレフィックス**（例: `/static/`） | 必要 | 必要 |
| `STATICFILES_DIRS` | **どこからファイルを探すか**（リスト）。アプリ外の共通ファイル用 | 任意 | 任意 |
| `STATIC_ROOT` | **`collectstatic` で集めた結果を置くディレクトリ**。本番で web サーバが直接配信する場所 | 通常不要 | **必須** |

イメージ：

```
[アプリの static/]  ─┐
[STATICFILES_DIRS] ─┼─→  collectstatic ─→  [STATIC_ROOT]
                                                  │
                                                  ▼
                                          Nginx などが配信
                                                  │
                                                  ▼
                                            STATIC_URL でアクセス
```

開発時は `runserver`/`runserver_plus` が動的に探して配信してくれるので `STATIC_ROOT` も `collectstatic` も不要。本番では Django は静的ファイル配信のための仕事を **しません**（パフォーマンスとセキュリティの理由）。代わりに `collectstatic` で1箇所に集約して、Nginx などに配信を任せます。

## 4-3. アプリ内 static の作り方とネームスペーシング

第1章で出てきた「アプリ名で1階層挟む」がここでも適用されます：

```
polls/
└── static/
    └── polls/         ← この階層を挟む
        ├── style.css
        ├── logo.png
        └── script.js
```

「`<app>/static/<app>/file` 構造にする」ことで、複数アプリで同じファイル名 (`style.css` など) が衝突するのを防ぎます。

`django.contrib.staticfiles` の **AppDirectoriesFinder** が、`INSTALLED_APPS` の各アプリの `static/` を自動で探します。`settings.py` を見ると：

```python
INSTALLED_APPS = [
    ...,
    "django.contrib.staticfiles",   ← これがいる
    ...,
]
```

がすでに入っているはずです（Django のデフォルト）。

## 4-4. テンプレートからの参照: `{% static %}` タグ

URL を直接書かず、**必ず `{% static %}` 経由で参照** します：

```django
{% load static %}

<link rel="stylesheet" href="{% static 'polls/style.css' %}">
<img src="{% static 'polls/logo.png' %}" alt="logo">
```

ポイント：
- ファイルの先頭に `{% load static %}` が必要
- `{% static '...' %}` の引数は **`STATIC_URL` から見たパス**（つまり `polls/style.css` であって `polls/static/polls/style.css` ではない）
- レンダリング結果は `<link href="/static/polls/style.css">`（`STATIC_URL=/static/` のとき）

なぜ直接 `/static/polls/style.css` と書かないか？ → `STATIC_URL` を `/static/` から `https://cdn.example.com/v2/` に変えたとき、全テンプレートを書き換える必要が出ます。`{% static %}` 経由ならテンプレートはそのまま、設定の1行を変えるだけで済みます。

## 4-5. `findstatic` でデバッグ

「ファイル参照してるのに表示されない…どこを見にいってる？」というとき：

```bash
uv run python manage.py findstatic polls/style.css
# Found 'polls/style.css' here:
#   /Users/.../polls/static/polls/style.css
```

複数の場所で見つかった場合は全部表示されます。意図しない方が優先されていないか確認できます。

## ハンズオン 4: polls に CSS を当てる

### 1. CSS ファイルを作成

`polls/static/polls/style.css` を新規作成：

```css
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    max-width: 720px;
    margin: 0 auto;
    padding: 1rem;
    color: #222;
    background: #fafafa;
}

header h1 a {
    color: inherit;
    text-decoration: none;
}

ul {
    list-style: none;
    padding: 0;
}

ul li {
    padding: 0.5rem 0;
    border-bottom: 1px solid #eee;
}

.error {
    color: #c00;
}

input[type="submit"] {
    background: #0066cc;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    cursor: pointer;
    border-radius: 4px;
}

footer {
    margin-top: 2rem;
    color: #999;
    text-align: center;
}
```

### 2. `base.html` から読み込み

`{% extends %}` を使っているテンプレートは、**`{% load static %}` を子テンプレートではなく `base.html` に書く** のがポイントです。テンプレートタグの load スコープはファイル単位なので、子で使うなら子にも load が必要、というのが原則ですが、base.html だけで static を参照するならそこだけで済みます：

```django
<!DOCTYPE html>
<html lang="ja">
{% load static %}
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}polls{% endblock %} | アンケートアプリ</title>
    <link rel="stylesheet" href="{% static 'polls/style.css' %}">
</head>
<body>
    ...
```

### 3. 動作確認

`uv run python manage.py runserver_plus` で起動して、ブラウザで `/polls/` を開いてください。

- フォントが変わり、中央寄せされ、リストの罫線が薄くなる → CSS が当たっている
- ブラウザの開発者ツール → Network タブで `style.css` が **200** で取得できているか確認
- うまく当たらないときは：
  - HTML ソースに `<link rel="stylesheet" href="/static/polls/style.css">` が出ているか
  - `uv run python manage.py findstatic polls/style.css` でファイルが見つかるか
  - ターミナルに `GET /static/polls/style.css HTTP/1.1" 200` が出ているか

### 4. CLI のクエリログに `static` の文字が出ていないことを確認

第2章の log フィルタは `information_schema` / `django_migrations` などしか除外していませんが、static ファイルの配信は **DB を使わない** ので、SQL ログには出ません。アクセスログの方に `GET /static/polls/style.css` として記録されます。

---

# 第5章 collectstatic と本番運用

## 5-1. なぜ collectstatic が必要？

開発時は Django が `<各アプリ>/static/` と `STATICFILES_DIRS` を毎リクエスト動的に探してくれます。が、本番でこれをやると：

1. **遅い**: ファイル探索のたびに Python が呼ばれる
2. **危険**: Django が静的ファイル配信用に作られていない
3. **散らばっている**: ファイルが各アプリのディレクトリに分散しているので、CDN や Nginx に「ここを配信して」と指定しづらい

そこで本番デプロイ前に **「全アプリの static フォルダを 1 か所に集める」** 操作が必要になります。それが `collectstatic` です。

## 5-2. settings に `STATIC_ROOT` を追加する

`config/settings.py` の `STATIC_URL = "static/"` の近くに：

```python
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"   # ← 追加
```

`staticfiles/` というディレクトリ名は慣習。`static/` だと `STATICFILES_DIRS` の1つと混同しやすいので避けます。

## 5-3. `collectstatic` を実行

```bash
uv run python manage.py collectstatic
```

確認プロンプトが出るので `yes`。すると：

```
N static files copied to '/Users/.../staticfiles', M post-processed.
```

`staticfiles/` の中身を見ると：

```
staticfiles/
├── admin/         ← django.contrib.admin の static
├── debug_toolbar/ ← debug_toolbar の static
├── django_extensions/
└── polls/
    └── style.css  ← さっき書いた CSS もここに集約された
```

`django.contrib.admin` や `debug_toolbar` のような外部アプリの CSS/JS も自動で集まります。

## 5-4. `.gitignore` に追加

`staticfiles/` はビルド成果物なので Git に入れません：

```
# .gitignore に追加
staticfiles/
```

## 5-5. 本番での配信オプション

`STATIC_ROOT` のファイルをブラウザに届ける方法は主に2つ：

### オプション A: Nginx などの reverse proxy

```nginx
server {
    location /static/ {
        alias /var/www/myproject/staticfiles/;
    }
    location / {
        proxy_pass http://django_app;
    }
}
```

最もパフォーマンスが良い王道。VPS や自前サーバ運用なら基本これ。

### オプション B: WhiteNoise (Django プロセスから直接配信)

Heroku / Railway / Render などの「Nginx 用意しづらい PaaS」では WhiteNoise が便利：

```bash
uv add whitenoise
```

```python
# settings.py
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",   # ← ここに追加
    "django.contrib.sessions.middleware.SessionMiddleware",
    ...
]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
```

`CompressedManifestStaticFilesStorage` は gzip 圧縮版を事前生成し、ファイル名にハッシュを埋め込むので **キャッシュ無効化（cache busting）** も自動でやってくれます。`style.css` が `style.abc123def.css` に化けるイメージ。

**重要**: WhiteNoise はあくまで **Static** 用。Media（次章）には使えません。

## ハンズオン 5: collectstatic を試す

### 1. `STATIC_ROOT` を追加

`config/settings.py` を編集：

```python
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
```

### 2. 実行

```bash
uv run python manage.py collectstatic
```

`yes` で確定 → `staticfiles/` ディレクトリが生まれます。

### 3. 中身を確認

```bash
ls staticfiles/
# admin/ debug_toolbar/ django_extensions/ polls/
```

`staticfiles/polls/style.css` が `polls/static/polls/style.css` のコピーであることを確認してください（`diff` でも `cmp` でもOK）。

### 4. `.gitignore` に追加

```
staticfiles/
```

### 5. （任意）一度消して collectstatic がやり直しになることを確認

```bash
rm -rf staticfiles
uv run python manage.py collectstatic --no-input
ls staticfiles/
```

`--no-input` を付けると確認プロンプトをスキップできます（CI / デプロイスクリプトで使う）。

---

# 第6章 Media Files — ユーザーアップロード

## 6-1. Static と Media の違い

| | Static | Media |
|---|---|---|
| 作る人 | 開発者 | エンドユーザー |
| バージョン管理 | する（Git に入れる） | しない（`.gitignore`） |
| 内容変更 | デプロイ時のみ | 実行時に増減 |
| 例 | UI のロゴ、CSS、JS | プロフィール画像、添付ファイル、投稿画像 |
| 開発時の配信 | `runserver` が自動 | `urls.py` で手動配信 |
| 本番配信 | Nginx / WhiteNoise / CDN | Nginx / S3 など（**WhiteNoise は不可**） |

ファイルが「開発者のもの」か「ユーザーのもの」かで設定がまるごと別になります。混ぜないこと。

## 6-2. 設定: `MEDIA_URL` と `MEDIA_ROOT`

```python
# settings.py
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
```

| 設定 | 意味 |
|---|---|
| `MEDIA_URL` | ブラウザがアクセスする URL のプレフィックス（例: `/media/`） |
| `MEDIA_ROOT` | アップロードされたファイルがサーバのファイルシステム上のどこに保存されるか |

## 6-3. 開発時の配信を urls.py に追加

**Django は本番でメディアファイルの配信をしません**（static と同じ理由）。開発時のみ、`runserver` でファイルを返せるように URLconf にショートカットを足します：

```python
# config/urls.py
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    ...
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

`if settings.DEBUG:` で囲ってあるので、`DEBUG=False`（本番）では何もしません。本番では Nginx 側で `location /media/` を `alias /var/.../media/` に向けるなどして配信します。

## 6-4. ImageField / FileField

モデルにファイルアップロード用のフィールドを足します：

```python
# models.py
class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date published")
    cover_image = models.ImageField(
        upload_to="polls/covers/",
        blank=True,
        null=True,
    )
```

| 引数 | 意味 |
|---|---|
| `upload_to="polls/covers/"` | `MEDIA_ROOT` 配下のサブディレクトリ。日付テンプレート `"polls/covers/%Y/%m/"` も使える |
| `blank=True` | フォーム上で必須にしない |
| `null=True` | DB に NULL を許可 |

`ImageField` は内部で `FileField` を継承していて、加えて「アップロードされたファイルが画像かどうか」を検証します。検証には **Pillow** ライブラリが必要：

```bash
uv add pillow
```

## 6-5. テンプレートでの表示

`{{ question.cover_image.url }}` で URL を取れます。`MEDIA_URL` プレフィックスがついた URL になります：

```django
{% if question.cover_image %}
    <img src="{{ question.cover_image.url }}" alt="{{ question.question_text }}">
{% endif %}
```

`{% if question.cover_image %}` でガードしないと、画像未設定の質問で `.url` がエラーになります。

## 6-6. アップロードフォーム

**`<form enctype="multipart/form-data">`** が必須。これがないとファイルがサーバまで届きません。`ModelForm` を使うのが手早いです：

```python
# forms.py (新規作成)
from django import forms
from .models import Question

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["question_text", "pub_date", "cover_image"]
```

```python
# views.py
from .forms import QuestionForm

def question_create(request):
    if request.method == "POST":
        form = QuestionForm(request.POST, request.FILES)   # ← request.FILES が肝
        if form.is_valid():
            form.save()
            return redirect("polls:index")
    else:
        form = QuestionForm()
    return render(request, "polls/question_form.html", {"form": form})
```

```django
{# polls/question_form.html #}
{% extends "polls/base.html" %}
{% block content %}
<form method="post" enctype="multipart/form-data">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">作成</button>
</form>
{% endblock %}
```

ポイント：
- `request.POST` と `request.FILES` の **両方** を `ModelForm` に渡す
- `enctype="multipart/form-data"` を form タグに必ず書く

## ハンズオン 6: 質問にカバー画像を追加

### 1. Pillow をインストール

```bash
uv add pillow
```

### 2. `Question` モデルに `cover_image` を追加

`polls/models.py`：

```python
class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date published")
    cover_image = models.ImageField(
        upload_to="polls/covers/",
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.question_text

    def was_published_recently(self):
        return self.pub_date >= timezone.now() - datetime.timedelta(days=1)
```

### 3. マイグレーション

```bash
uv run python manage.py makemigrations polls
uv run python manage.py migrate
```

### 4. settings に MEDIA を追加

`config/settings.py`、`STATIC_URL` の近くに：

```python
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
```

### 5. urls.py に開発時配信を追加

`config/urls.py`：

```python
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("polls/", include("polls.urls", namespace="polls")),
    path("todo/", include("todo.urls", namespace="todo")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

（既存の `urlpatterns` の構成は環境ごとに違うので、自分のに合わせて末尾に if 文を追加してください。）

### 6. `.gitignore` に media を追加

```
staticfiles/
media/
```

### 7. admin から画像アップロード

`uv run python manage.py runserver_plus` → `/admin/polls/question/` → 既存の質問の編集画面に `cover_image` フィールドが出ています。手元の適当な PNG/JPG をアップロードして保存。

ファイルシステム上 `media/polls/covers/<filename>.png` ができていることを確認：

```bash
ls media/polls/covers/
```

### 8. テンプレートで表示

`polls/templates/polls/_question_item.html` を修正：

```django
<li>
    {% if question.cover_image %}
        <img src="{{ question.cover_image.url }}" alt="" style="height: 2em; vertical-align: middle;">
    {% endif %}
    <a href="{% url 'polls:detail' question.id %}">{{ question.question_text }}</a>
    <small>（{{ question.pub_date|date:"Y-m-d" }} 公開）</small>
</li>
```

`detail.html` にも大きく表示する block を追加：

```django
{% block content %}
    <h2>{{ question.question_text }}</h2>

    {% if question.cover_image %}
        <img src="{{ question.cover_image.url }}" alt="" style="max-width: 100%;">
    {% endif %}
    ...
```

### 9. 動作確認

ブラウザで `/polls/` を再読み込み → 画像をアップロードした質問にサムネが付き、`/polls/<id>/` で大きく表示されれば成功です。

ブラウザの開発者ツール → Network タブで `GET /media/polls/covers/xxx.png HTTP/1.1 200` が出ているはずです。

---

# 第7章 知っておくべきフィルタとタグ

最低限これだけ覚えておけば9割の場面で困りません。

## 7-1. 文字列系フィルタ

```django
{{ "django"|upper }}                        {# DJANGO #}
{{ "DJANGO"|lower }}                        {# django #}
{{ "hello world"|title }}                   {# Hello World #}
{{ "long text..."|truncatechars:5 }}        {# long… #}
{{ "long text..."|truncatewords:2 }}        {# long text… #}
{{ "  spaces  "|strip }}                    {# spaces (Django 5+) #}
{{ html_value|escape }}                     {# &lt;b&gt;... #}
{{ html_value|safe }}                       {# <b>...（エスケープしない）#}
{{ html_value|striptags }}                  {# タグ削除 #}
{{ "title bar"|slugify }}                   {# title-bar #}
```

## 7-2. 数値系

```django
{{ price|floatformat:2 }}        {# 99.99 #}
{{ items|length }}               {# 個数 #}
{{ count }} 件{{ count|pluralize:"s" }}     {# 英語の複数形 #}
{{ value|add:5 }}                {# value + 5 #}
```

`pluralize` は単数/複数を切り替えるフィルタですが、日本語では使い道が少ないです（英語の "1 item" / "5 items" 切り替えに便利）。

## 7-3. 日付・時間

```django
{{ pub_date|date:"Y-m-d" }}      {# 2026-05-15 #}
{{ pub_date|date:"Y年m月d日" }}   {# 2026年05月15日 #}
{{ pub_date|date:"H:i" }}        {# 14:30 #}
{{ pub_date|date:"D" }}          {# Fri #}
{{ pub_date|timesince }}         {# 3 hours, 2 minutes #}
{{ pub_date|naturaltime }}       {# "1 hour ago"（humanize 必要）#}
```

`naturaltime` は `django.contrib.humanize` を `INSTALLED_APPS` に追加して `{% load humanize %}` してから使います。

## 7-4. デフォルト・存在チェック

```django
{{ value|default:"未設定" }}      {# value が空 (None, "", 0 など) のとき "未設定" #}
{{ value|default_if_none:"-" }}   {# value が None のときだけ "-" #}
{% firstof var1 var2 "default" %} {# 最初の真の値 #}
```

## 7-5. リスト系

```django
{{ items|join:", " }}             {# a, b, c #}
{{ items|first }}
{{ items|last }}
{{ items|slice:":3" }}            {# 最初の3件（Python のスライス文法）#}
```

## 7-6. 必須タグ

### `{% url %}`

```django
{% url 'polls:detail' question.id %}        {# 単純な引数渡し #}
{% url 'polls:detail' question_id=q.id %}   {# キーワード引数 #}
{% url 'polls:index' as index_url %}        {# 変数に格納 #}
<a href="{{ index_url }}">戻る</a>
```

### `{% with %}`

長い式の結果を一時変数に：

```django
{% with total=question.choices.count %}
    合計 {{ total }} 件の選択肢
{% endwith %}
```

### `{% widthratio %}`

棒グラフのような比率計算：

```django
{# choice.votes / total_votes * 100 をピクセルとして書き出す #}
<div style="width: {% widthratio choice.votes total_votes 300 %}px;"></div>
```

「`current_value` / `max_value` * `scale`」を計算して整数で返してくれます。

### `{% cycle %}`

縞模様のテーブルなど：

```django
{% for choice in choices %}
    <tr class="{% cycle 'odd' 'even' %}">...</tr>
{% endfor %}
```

### `{% csrf_token %}`

POST フォームに **必ず** 入れます。これがないと Django が 403 を返します。

### `{% autoescape off %}`

```django
{% autoescape off %}
    {{ trusted_html }}
{% endautoescape %}
```

XSS の温床なので、本当に信頼できるソースに限定。基本は `|safe` の方が「ここだけ」感が出て安全です。

## ハンズオン 7: results.html を整える

`polls/templates/polls/results.html` を、`widthratio` で簡易な棒グラフを描く形に拡張してみます：

```django
{% extends "polls/base.html" %}

{% block title %}{{ question.question_text }} の結果{% endblock %}

{% block content %}
    <h2>{{ question.question_text }} の結果</h2>

    {% with total=question.choices.all|length %}
        <p>{{ question.pub_date|date:"Y-m-d H:i" }} 公開</p>

        {# 合計票数を計算するために choices をループしながら集計 #}
        {% with choices=question.choices.all %}
            <ul>
                {% for choice in choices %}
                    <li>
                        <strong>{{ choice.choice_text }}</strong>:
                        {{ choice.votes }} 票
                        <div style="background:#0066cc;height:12px;width:{% widthratio choice.votes 50 300 %}px;"></div>
                    </li>
                {% endfor %}
            </ul>
        {% endwith %}
    {% endwith %}

    <p>
        <a href="{% url 'polls:detail' question.id %}">もう一度投票</a> |
        <a href="{% url 'polls:index' %}">一覧に戻る</a>
    </p>
{% endblock %}
```

`widthratio choice.votes 50 300` は「`votes` が 50 のとき 300px、25 のとき 150px」になる横棒です。max が 50 票決め打ちなのは仮の値。次の章で「max を動的に計算するカスタムタグ」を作ります。

---

# 第8章 カスタムテンプレートタグ / フィルタ

## 8-1. ビルトインで足りない場面

たとえば「質問の総得票数を表示したい」とき：

```django
{# 全選択肢の votes を合計したい — でも DTL に sum がない #}
{{ question.choices.all|sum_of:"votes" }}    {# 想像上の構文 #}
```

DTL は **意図的にロジックを書けないように制限されている** ので、こういう「集計したい」「ややこしい変換をしたい」は **ビューで計算してテンプレートに渡す** か、**カスタムテンプレートタグ/フィルタを定義する** のが正攻法です。

ビュー側で `total = sum(c.votes for c in choices)` を計算してコンテキストに足すのが一番素直ですが、複数テンプレートで使い回すならカスタムタグの方が DRY です。

## 8-2. ディレクトリ構成

カスタムタグを定義するには、アプリ内に **`templatetags/` という名前のディレクトリ** を作って、そこに Python ファイルを置きます：

```
polls/
├── templatetags/
│   ├── __init__.py        ← 空ファイル（必須）
│   └── polls_tags.py      ← ここにタグ/フィルタを書く
```

ファイル名（`polls_tags`）が `{% load %}` で使う名前になります。

## 8-3. カスタムフィルタ

```python
# polls/templatetags/polls_tags.py
from django import template

register = template.Library()

@register.filter
def total_votes(question):
    """Question の全 Choice の votes を合計する。"""
    return sum(choice.votes for choice in question.choices.all())
```

テンプレート側：

```django
{% load polls_tags %}

合計 {{ question|total_votes }} 票
```

フィルタは **第1引数が `|` の左** にあるオブジェクト、第2引数が `:` の後ろ、という決まり。

引数付きフィルタも書けます：

```python
@register.filter
def vote_percentage(choice, total):
    if not total:
        return 0
    return round(choice.votes / total * 100, 1)
```

```django
{{ choice|vote_percentage:total }}%
```

## 8-4. シンプルタグ

「引数を複数取って計算結果を返したい」場合は `simple_tag` が便利：

```python
@register.simple_tag
def percentage(part, whole):
    if not whole:
        return 0
    return round(part / whole * 100, 1)
```

```django
{% percentage choice.votes total %}%
```

シンプルタグは **キーワード引数** や **`as`** で変数代入もできます：

```django
{% percentage choice.votes total as p %}
<div>{{ p }}%</div>
```

## 8-5. インクルージョンタグ

「タグ呼び出し1回でテンプレートをレンダリングして埋め込みたい」場合：

```python
@register.inclusion_tag("polls/_choice_bar.html")
def choice_bar(choice, total):
    return {
        "label": choice.choice_text,
        "votes": choice.votes,
        "percent": (choice.votes / total * 100) if total else 0,
    }
```

```django
{# polls/templates/polls/_choice_bar.html #}
<div class="choice-bar">
    <strong>{{ label }}</strong>
    <span>{{ votes }} 票 ({{ percent|floatformat:1 }}%)</span>
    <div style="background:#0066cc;height:8px;width:{{ percent }}%;"></div>
</div>
```

使い方：

```django
{% load polls_tags %}

{% for choice in question.choices.all %}
    {% choice_bar choice total %}
{% endfor %}
```

インクルージョンタグの戻り値は **そのテンプレートに渡るコンテキスト dict**。再利用しやすい「タグ風のコンポーネント」が作れます。

## ハンズオン 8: results.html をカスタムタグで作り直す

### 1. ディレクトリとファイルを作る

```bash
mkdir polls/templatetags
touch polls/templatetags/__init__.py
touch polls/templatetags/polls_tags.py
```

### 2. `polls/templatetags/polls_tags.py` を書く

```python
from django import template

register = template.Library()


@register.filter
def total_votes(question):
    """Question の全 Choice の votes を合計する。"""
    return sum(choice.votes for choice in question.choices.all())


@register.inclusion_tag("polls/_choice_bar.html")
def choice_bar(choice, total):
    percent = (choice.votes / total * 100) if total else 0
    return {
        "label": choice.choice_text,
        "votes": choice.votes,
        "percent": percent,
    }
```

### 3. `polls/templates/polls/_choice_bar.html` を作る

```django
<li style="margin-bottom: 0.8em;">
    <strong>{{ label }}</strong>:
    {{ votes }} 票 ({{ percent|floatformat:1 }}%)
    <div style="background:#0066cc;height:10px;width:{{ percent|floatformat:0 }}%;max-width:100%;border-radius:2px;"></div>
</li>
```

### 4. `results.html` を書き換え

```django
{% extends "polls/base.html" %}
{% load polls_tags %}

{% block title %}{{ question.question_text }} の結果{% endblock %}

{% block content %}
    <h2>{{ question.question_text }} の結果</h2>

    {% if question.cover_image %}
        <img src="{{ question.cover_image.url }}" alt="" style="max-width: 100%;">
    {% endif %}

    <p>合計 <strong>{{ question|total_votes }}</strong> 票</p>

    <ul style="list-style: none; padding: 0;">
        {% with total=question|total_votes %}
            {% for choice in question.choices.all %}
                {% choice_bar choice total %}
            {% endfor %}
        {% endwith %}
    </ul>

    <p>
        <a href="{% url 'polls:detail' question.id %}">もう一度投票</a> |
        <a href="{% url 'polls:index' %}">一覧に戻る</a>
    </p>
{% endblock %}
```

### 5. 動作確認

ブラウザで `/polls/1/results/` を開いて、選択肢ごとに票数と棒グラフが表示されることを確認してください。

> **注意**: `{% load polls_tags %}` を書き忘れると `{% choice_bar %}` で `TemplateSyntaxError: Invalid block tag` が出ます。継承先のファイルでカスタムタグを使うなら、その **継承先ファイル自身に load を書く必要があります**（base.html に書いても効きません）。

> **重要**: `templatetags/__init__.py` を作り忘れると、Python が `templatetags` をパッケージとして認識せず、`{% load polls_tags %}` で `'polls_tags' is not a registered tag library` というエラーになります。

---

# 第9章 コンテキストプロセッサ

## 9-1. なぜ必要？

「全テンプレートで `site_name` 変数を使いたい」というとき、ビューを書くたびに `context["site_name"] = "..."` するのは面倒です。**コンテキストプロセッサ** は **全テンプレートに自動で変数を注入する仕組み** です。

例: `{{ user }}` や `{{ request }}` がどのテンプレートでも書ける理由は、Django のビルトインコンテキストプロセッサがそれをやっているからです。

`config/settings.py:77-80`：

```python
"context_processors": [
    "django.template.context_processors.request",   # → {{ request }} を有効化
    "django.contrib.auth.context_processors.auth",  # → {{ user }} と {{ perms }} を有効化
    "django.contrib.messages.context_processors.messages",
],
```

## 9-2. カスタムコンテキストプロセッサを書く

「サイト名やバージョン情報を全テンプレートに渡したい」という場合：

### 1. プロセッサ本体を書く

```python
# polls/context_processors.py
def site_metadata(request):
    return {
        "site_name": "アンケートアプリ",
        "site_version": "0.1.0",
    }
```

**型のお作法**: `request` を1引数で受け取り、コンテキストに足したい変数の dict を返す。それだけ。

### 2. settings に登録

```python
# config/settings.py
TEMPLATES = [
    {
        ...
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "polls.context_processors.site_metadata",   # ← 追加
            ],
        },
    },
]
```

### 3. テンプレートで使う

```django
{# base.html #}
<title>{% block title %}polls{% endblock %} | {{ site_name }} v{{ site_version }}</title>
```

ビュー側で何もしなくても `{{ site_name }}` が使えるようになります。

## 9-3. 使いすぎ注意

便利な反面、**全リクエストで毎回呼ばれる** ので：
- 重い DB クエリを入れない
- 例外で死ぬような処理を入れない
- グローバル変数の温床になる（どこから値が来てるか分かりづらい）

「本当に全テンプレートで必要な値」だけに留めるのがコツです。サイト名、ユーザー、ナビゲーション項目、フィーチャーフラグくらい。

## ハンズオン 9: site_metadata を導入

### 1. `polls/context_processors.py` を作成

```python
def site_metadata(request):
    return {
        "site_name": "アンケートアプリ",
        "site_version": "0.1.0",
    }
```

### 2. settings に登録

`config/settings.py` の `TEMPLATES.OPTIONS.context_processors` に追加：

```python
"polls.context_processors.site_metadata",
```

### 3. `base.html` で使う

```django
<title>{% block title %}polls{% endblock %} | {{ site_name }}</title>
...
<footer>
    <p><small>&copy; 2026 {{ site_name }} v{{ site_version }}</small></p>
</footer>
```

### 4. 動作確認

ブラウザで polls の任意のページを開く → タイトルとフッターに「アンケートアプリ」「v0.1.0」が出ていれば成功。

---

# 付録 A. 完成形のファイルツリー

ハンズオンを完走するとこうなります：

```
roadmap-sh-django/
├── config/
│   ├── settings.py            # STATIC_URL, STATIC_ROOT, MEDIA_URL, MEDIA_ROOT, context_processors
│   ├── urls.py                # if DEBUG: static(MEDIA_URL, ...) を追加
│   └── ...
├── polls/
│   ├── context_processors.py  # ← 第9章
│   ├── forms.py               # ← (任意) 第6章
│   ├── models.py              # cover_image を追加
│   ├── views.py
│   ├── static/
│   │   └── polls/
│   │       └── style.css      # ← 第4章
│   ├── templates/
│   │   └── polls/
│   │       ├── base.html              # ← 第2章
│   │       ├── _question_item.html    # ← 第3章
│   │       ├── _choice_bar.html       # ← 第8章
│   │       ├── index.html
│   │       ├── detail.html
│   │       └── results.html
│   └── templatetags/                  # ← 第8章
│       ├── __init__.py
│       └── polls_tags.py
├── staticfiles/                       # ← collectstatic の結果（.gitignore）
├── media/                             # ← アップロード先（.gitignore）
└── docs/
    └── 03-templates-static-media.md   # ← このドキュメント
```

---

# 付録 B. よくあるハマりどころチェックリスト

| 症状 | 原因 | 対処 |
|---|---|---|
| `{% url 'polls:detail' %}` で `NoReverseMatch` | URL に引数が足りない / 多すぎる | `urls.py` の `path()` の引数と一致するか確認 |
| `{% static '...' %}` が `{% load static %}` を呼べと言う | ファイル先頭で load し忘れ | `{% extends %}` の **直後** くらいに `{% load static %}` |
| 画像が `<img src="">` で空 URL | `{{ obj.image.url }}` を画像未設定で呼んだ | `{% if obj.image %}` で囲む |
| Media ファイルが 404 | `urls.py` の `if settings.DEBUG: ... static(MEDIA_URL, ...)` を忘れた | 第6章 6-3 を確認 |
| ImageField 保存時 `Pillow が必要` エラー | `pillow` 未インストール | `uv add pillow` |
| カスタムタグが「Invalid block tag」 | 該当ファイルで `{% load polls_tags %}` を忘れた / `templatetags/__init__.py` がない | 両方確認 |
| `findstatic` で複数ヒット | アプリ間でファイル名衝突 | `<app>/static/<app>/...` 構造に統一 |
| 本番で CSS が当たらない | `collectstatic` 未実行 / Nginx 設定不備 | `python manage.py collectstatic` + 静的配信側設定確認 |
| アップロードしたファイルが見えない | 開発: urls.py の `static()` 忘れ。本番: Nginx の `/media/` 設定忘れ | 環境ごとに確認 |
| `POST` フォームで `403 CSRF verification failed` | `{% csrf_token %}` を form 内に書き忘れ | フォームの中に必ず入れる |
| `<form>` でファイルが届かない | `enctype="multipart/form-data"` を書き忘れ | form タグの属性を確認 |

---

# 付録 C. 開発時 vs 本番、配信の仕組みまとめ

```
─────── 開発時 (DEBUG=True) ──────────────────────

  ブラウザ ──/static/polls/style.css──→ Django (runserver)
                                          │
                                          ▼
                                  AppDirectoriesFinder で
                                  polls/static/polls/style.css を発見
                                          │
                                          ▼
                                      ファイル送信

  ブラウザ ──/media/polls/covers/x.png──→ Django (runserver)
                                          │
                                          ▼  if settings.DEBUG: urlpatterns += static(...)
                                  MEDIA_ROOT/polls/covers/x.png
                                          │
                                          ▼
                                      ファイル送信


─────── 本番 (DEBUG=False) ──────────────────────

  ブラウザ ──/static/polls/style.abc.css──→ Nginx
                                            │
                                            ▼  location /static/ alias STATIC_ROOT
                                    /var/www/.../staticfiles/polls/style.abc.css
                                            │
                                            ▼
                                        ファイル送信
                                  (Django は1ミリも関与しない)

  ブラウザ ──/media/polls/covers/x.png──→ Nginx
                                          │
                                          ▼  location /media/ alias MEDIA_ROOT
                                  /var/www/.../media/polls/covers/x.png
                                          │
                                          ▼
                                      ファイル送信
                                  (大規模なら S3 などへ)
```

開発時の便利さに慣れると本番で詰まりやすいので、**「DEBUG=False のとき Django は静的/メディアファイル配信をしない」** は必ず覚えてください。

---

# 付録 D. 参考リンク

- [How to manage static files](https://docs.djangoproject.com/en/6.0/howto/static-files/) - Django 公式
- [Templates](https://docs.djangoproject.com/en/6.0/topics/templates/) - Django 公式
- [Working with Static and Media Files in Django](https://testdriven.io/blog/django-static-files/) - testdriven.io
- [The Ultimate Guide to Django Templates](https://blog.jetbrains.com/pycharm/2025/02/the-ultimate-guide-to-django-templates/) - JetBrains
- [Built-in template tags and filters](https://docs.djangoproject.com/en/6.0/ref/templates/builtins/) - 全ビルトインの索引（よく見る）
- [WhiteNoise](https://whitenoise.readthedocs.io/) - 本番で WhiteNoise を使うときに

---

ここまで完走おつかれさまでした。次は **フォーム（Django Forms）** か **認証（auth）** あたりに進むと、今書いた templates / static / media が活きてきます。
