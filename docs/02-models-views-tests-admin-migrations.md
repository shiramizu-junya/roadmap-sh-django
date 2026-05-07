# モデル・マイグレーション・Admin・ビュー・テスト 完全入門

> **このドキュメントの読み方**
> 上から順に読み、コードブロックを **自分の手で** プロジェクトに書き写しながら進めてください。各章末の「ハンズオン」が、その章の知識を使って `polls/` アプリを一段ずつ完成形に近づける作りになっています。完走すると `polls/` が「投票アプリ」として動作し、テストもグリーンになります。
>
> **前提**: `docs/01-manage-py-and-urls.md` を完了している状態。`polls/` の URL ルーティングは設定済みだが、ビューはダミーの `HttpResponse` を返しているだけ — のところからスタートします。

---

## このドキュメントで作るもの

完走後の `polls/` の振る舞い:

| URL | やること |
|---|---|
| `/polls/` | 最近公開された質問の一覧を表示 |
| `/polls/<id>/` | 質問の詳細と選択肢を表示、投票フォームあり |
| `/polls/<id>/vote/` | POST を受けて投票数を +1、結果ページへリダイレクト |
| `/polls/<id>/results/` | 投票結果を表示 |
| `/admin/` | スタッフが質問・選択肢を CRUD できる |

完走後に身につく知識:
- **モデル定義**: フィールド型、`ForeignKey`、`Meta`、`__str__`、カスタムメソッド
- **マイグレーション**: `makemigrations`/`migrate` の役割分担、`sqlmigrate` で SQL 検査、ロールバック、データマイグレーション
- **Admin カスタマイズ**: `list_display`、`list_filter`、`search_fields`、`fieldsets`、`inlines`、`@admin.register`
- **実用ビュー**: `render()`、`get_object_or_404()`、POST ハンドリング、CSRF
- **テンプレート**: テンプレートタグ、フィルタ、`{% url %}`、`{% csrf_token %}`
- **自動テスト**: `TestCase`、`self.client`、`assertContains`、`assertQuerySetEqual`、テストデータ作成

---

# 第1章 models.py — データの形を定義する

## 1-1. モデルとは

`models.py` は **アプリが扱うデータの設計図** です。各クラスが DB のテーブルに対応し、各クラス属性がカラムに対応します。

```python
from django.db import models

class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date published")
```

ポイント:
- `models.Model` を継承する → これだけで Django が DB マッピングや ORM を提供
- 主キー (`id`) は **自動追加** されるので書かない
- テーブル名は **自動で `<app>_<model>`**（上の例なら `polls_question`）

## 1-2. フィールド型の早見表

| フィールド | 用途 | SQL 型（MySQL） |
|---|---|---|
| `CharField(max_length=N)` | 短いテキスト（必ず `max_length` 必須） | `VARCHAR(N)` |
| `TextField` | 長文 | `LONGTEXT` |
| `IntegerField` | 整数 | `INT` |
| `BigIntegerField` | 大きな整数 | `BIGINT` |
| `FloatField` | 浮動小数 | `DOUBLE` |
| `DecimalField(max_digits=N, decimal_places=M)` | 高精度小数（金額など） | `DECIMAL` |
| `BooleanField` | true/false | `TINYINT(1)` |
| `DateField` | 日付 | `DATE` |
| `DateTimeField` | 日時 | `DATETIME` |
| `TimeField` | 時刻 | `TIME` |
| `EmailField` | メールアドレス（バリデーション付き） | `VARCHAR(254)` |
| `URLField` | URL（バリデーション付き） | `VARCHAR(200)` |
| `SlugField` | URL 用スラッグ（`my-first-post` など） | `VARCHAR(50)` |
| `FileField` / `ImageField` | アップロードファイル（実体は別場所、DB にはパス） | `VARCHAR(100)` |
| `JSONField` | JSON | `JSON` |
| `UUIDField` | UUID | `CHAR(32)` |

> **「金額に Float を使わない」** は鉄則。誤差で 1 円ずれる事故が起きます。`DecimalField(max_digits=10, decimal_places=2)` を使う。

## 1-3. フィールドオプション

```python
class Product(models.Model):
    # null: DB レベルで NULL を許可するか（数値・日時に使う）
    discount = models.IntegerField(null=True)

    # blank: フォーム検証で空欄を許可するか（フォーム/Admin の制御）
    notes = models.CharField(max_length=200, blank=True)

    # default: デフォルト値
    status = models.CharField(max_length=10, default="draft")

    # unique: ユニーク制約
    sku = models.CharField(max_length=20, unique=True)

    # db_index: インデックスを付ける（検索が速くなる）
    name = models.CharField(max_length=100, db_index=True)

    # choices: 取り得る値を限定
    PRIORITY_CHOICES = [("low", "低"), ("mid", "中"), ("high", "高")]
    priority = models.CharField(max_length=4, choices=PRIORITY_CHOICES, default="mid")

    # verbose_name / help_text: Admin の表示
    title = models.CharField("タイトル", max_length=100, help_text="一覧に表示される文字列")
```

> **`null=True` と `blank=True` の使い分け**:
> - `null=True` → **DB の話**（`NULL` を許す）。数値・日付・FK で使う
> - `blank=True` → **フォームの話**（空欄を許す）。Admin やフォームのバリデーションで効く
> - `CharField` / `TextField` で「任意入力」にしたいときは **`blank=True` だけ** 付ける（空文字 `""` を入れる方が NULL より扱いやすいため、`null=True` は要らない）

## 1-4. リレーション

### ForeignKey（多対一）

「Choice は Question に属する」のような関係:

```python
class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)
```

`on_delete` の選択肢:

| 値 | 振る舞い | 使う場面 |
|---|---|---|
| `CASCADE` | 親が消えたら子も消える | 「親と運命を共にする」もの（質問 → 選択肢など） |
| `PROTECT` | 親に子がいると親を消せない | 重要データ（注文 → 商品など） |
| `SET_NULL` | 親が消えたら子の FK を NULL に | `null=True` も必要 |
| `SET_DEFAULT` | 親が消えたらデフォルト値に | `default=...` も必要 |
| `DO_NOTHING` | DB 任せ（危険、ほぼ使わない） | レガシー対応のみ |

逆参照は **デフォルトで `<モデル名小文字>_set`** です:

```python
question = Question.objects.get(pk=1)
question.choice_set.all()              # この質問のすべての選択肢
question.choice_set.create(choice_text="赤", votes=0)
```

`related_name` を指定すると名前を変えられます:

```python
question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
# → question.choices.all() で参照できるようになる
```

### ManyToManyField（多対多）

```python
class Topping(models.Model):
    name = models.CharField(max_length=100)

class Pizza(models.Model):
    name = models.CharField(max_length=100)
    toppings = models.ManyToManyField(Topping)

# 中間テーブル (pizza_toppings) は Django が自動で作る
pizza.toppings.add(cheese)
pizza.toppings.remove(cheese)
pizza.toppings.all()
```

中間テーブルに追加カラムが必要なら `through=` で自前モデルを使います（メンバーシップに加入日を持たせるなど）。

### OneToOneField（一対一）

ユーザープロフィール拡張などで使う。`ForeignKey(unique=True)` とほぼ同じ。

```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
```

## 1-5. Meta クラス

モデルそのもののメタ情報を定義:

```python
class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date published")

    class Meta:
        ordering = ["-pub_date"]                # デフォルトの並び順（QuerySet で自動適用）
        verbose_name = "質問"
        verbose_name_plural = "質問"            # 日本語は単複同形
        db_table = "polls_question"             # テーブル名を明示（普段不要）
        indexes = [
            models.Index(fields=["pub_date"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["question_text"], name="uniq_question_text"),
        ]
```

`ordering` を入れておくと、`Question.objects.all()` が暗黙に並んだ状態で返ってくるので、テンプレート側で並べ替えを書く必要が減ります。

## 1-6. `__str__` とカスタムメソッド

```python
class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date published")

    def __str__(self):
        return self.question_text                  # Admin / shell で識別しやすくなる

    def was_published_recently(self):
        """公開日が直近 24 時間以内か。"""
        import datetime
        from django.utils import timezone
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now
```

`__str__` は **必ず書く** くらいの気持ちで OK。書かないと Admin で `Question object (1)` のような意味不明な表示になります。

## ハンズオン① Question / Choice モデルを書く

### あなたが行うこと

1. `polls/models.py` を開く。
2. 以下のコードを書く（コピペでも、手で打ってもよい）:

```python
import datetime
from django.db import models
from django.utils import timezone


class Question(models.Model):
    question_text = models.CharField("質問文", max_length=200)
    pub_date = models.DateTimeField("公開日時")

    class Meta:
        ordering = ["-pub_date"]
        verbose_name = "質問"
        verbose_name_plural = "質問"

    def __str__(self):
        return self.question_text

    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now


class Choice(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="choices",
    )
    choice_text = models.CharField("選択肢", max_length=200)
    votes = models.IntegerField("投票数", default=0)

    class Meta:
        ordering = ["id"]
        verbose_name = "選択肢"
        verbose_name_plural = "選択肢"

    def __str__(self):
        return self.choice_text
```

3. ファイル保存。次の章 (`makemigrations` / `migrate`) で DB に反映します。

> **この時点ではまだ DB に何も反映されていません**。`models.py` は「設計図」を更新しただけ。次章でマイグレーションを作って実際にテーブルを作ります。

---

# 第2章 マイグレーション — モデル変更を DB に反映する

## 2-1. makemigrations と migrate の役割分担

| コマンド | 何をする | 影響範囲 |
|---|---|---|
| `makemigrations` | `models.py` を読み、前回との差分を検出して **マイグレーションファイル** (`0001_initial.py` など) を生成 | プロジェクトのファイル（git 管理） |
| `migrate` | マイグレーションファイルを順に実行して **DB のスキーマを変更** | DB（git 管理外） |

「設計図を更新する」のと「設計図に従って実物を建てる」が分かれている、と覚えるのが分かりやすいです。

> **マイグレーションファイルは必ずコミット** します。設計図がチームで共有されないと、各自の DB がバラバラになります。

## 2-2. マイグレーションファイルの中身

`polls/migrations/0001_initial.py` を作るとこんな感じになります（これを **手で書くことはほぼない**、自動生成を読めれば OK）:

```python
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True

    dependencies = []   # 他のマイグレーションへの依存

    operations = [
        migrations.CreateModel(
            name="Question",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True)),
                ("question_text", models.CharField(max_length=200)),
                ("pub_date", models.DateTimeField(verbose_name="公開日時")),
            ],
            options={
                "verbose_name": "質問",
                "ordering": ["-pub_date"],
            },
        ),
        migrations.CreateModel(
            name="Choice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True)),
                ("choice_text", models.CharField(max_length=200)),
                ("votes", models.IntegerField(default=0)),
                ("question", models.ForeignKey(
                    on_delete=models.deletion.CASCADE,
                    related_name="choices",
                    to="polls.question",
                )),
            ],
        ),
    ]
```

主な操作:

| 操作 | 用途 |
|---|---|
| `CreateModel` | 新規テーブル作成 |
| `DeleteModel` | テーブル削除 |
| `AddField` | カラム追加 |
| `RemoveField` | カラム削除 |
| `AlterField` | カラム型・オプション変更 |
| `RenameField` / `RenameModel` | リネーム |
| `RunPython` | データ移行（任意の Python を実行） |
| `RunSQL` | 任意の SQL 実行 |

## 2-3. sqlmigrate — 適用前に SQL を見る

危険なマイグレーションを本番に流す前に **必ず** これで SQL を見ましょう。

```bash
uv run python manage.py sqlmigrate polls 0001
```

出力される `CREATE TABLE` や `ALTER TABLE` を読み、想定外のことが起きないか確認します。例えば「`AlterField` が裏で `DROP COLUMN` + `ADD COLUMN` になっていないか」「巨大テーブルへの `ALTER` がロックを取らないか」など、ミスを未然に防げます。

## 2-4. ロールバック

「`0003` を作ったけど取り消したい」場合、`0002` を指定するとそこまで戻せます:

```bash
uv run python manage.py migrate polls 0002        # 0003 を逆方向に実行
uv run python manage.py migrate polls zero        # アプリのテーブルを全消し（戻し）
```

ただし `RunSQL` などの不可逆操作は **逆方向 SQL を自分で書いていない限り戻せません**。

## 2-5. データマイグレーション

「カラムの値を一括更新する」「FK の関係を組み直す」など、**スキーマ変更ではなくデータ変更** を伴うときに使います。

```bash
uv run python manage.py makemigrations --empty polls --name backfill_votes
```

生成された空マイグレーションに `RunPython` を書きます:

```python
from django.db import migrations

def backfill_votes(apps, schema_editor):
    # ここで apps.get_model を使うのが鉄則。直 import すると将来壊れる
    Choice = apps.get_model("polls", "Choice")
    Choice.objects.filter(votes__isnull=True).update(votes=0)


def reverse_backfill(apps, schema_editor):
    pass   # 戻す必要がなければ no-op


class Migration(migrations.Migration):
    dependencies = [("polls", "0001_initial")]
    operations = [migrations.RunPython(backfill_votes, reverse_backfill)]
```

> **`apps.get_model("polls", "Choice")`** を使う理由: 将来モデルが変わった後に過去のマイグレーションを再実行しても、その時点の Choice の状態でアクセスできる。直 `from .models import Choice` だと将来壊れる。

## 2-6. ベストプラクティス

- **モデルを変えたら必ず `makemigrations`**（DB 直触りは禁止）
- **マイグレーションファイルは git にコミット**
- **本番反映前に必ず `sqlmigrate` で確認**
- **巨大テーブルへの `ALTER` は注意**（`AddField` で `default=` を指定すると全行更新が走る）
- **頻繁に作って小さく保つ**（後でまとめれば良いので、こまめに作る方が安全）
- **`squashmigrations` で過去を整理**（マイグレーションが 50 個超えたら検討）

## ハンズオン② polls の初期マイグレーション

### あなたが行うこと

1. マイグレーションファイルを生成:

```bash
uv run python manage.py makemigrations polls
```

期待出力:
```
Migrations for 'polls':
  polls/migrations/0001_initial.py
    + Create model Question
    + Create model Choice
```

2. 適用前の SQL を確認:

```bash
uv run python manage.py sqlmigrate polls 0001
```

`CREATE TABLE polls_question (...)`、`CREATE TABLE polls_choice (...)`、外部キー制約が表示されるはず。

3. DB に適用:

```bash
uv run python manage.py migrate
```

4. 適用状況を確認:

```bash
uv run python manage.py showmigrations polls
```

`[X] 0001_initial` になっていれば OK。

5. shell で動作確認:

```bash
uv run python manage.py shell
```

```python
from django.utils import timezone
from polls.models import Question, Choice

# 質問を作る
q = Question.objects.create(
    question_text="今日の朝食は？",
    pub_date=timezone.now(),
)

# 選択肢を追加（related_name="choices" を活かす）
q.choices.create(choice_text="パン", votes=0)
q.choices.create(choice_text="ご飯", votes=0)
q.choices.create(choice_text="抜いた", votes=0)

# 確認
Question.objects.all()
q.choices.all()
q.choices.count()
q.was_published_recently()    # True
```

これで polls の DB 側の準備は完了です。

---

# 第3章 admin.py — 管理画面を整える

## 3-1. なぜ Admin を覚えるか

Django Admin は **本体機能とほぼ同等の手間で使える管理画面** で、以下の場面で実務でも便利です:

- 開発中にデータを手作業で投入・修正する
- 運用後、ユーザーや権限を切り替える
- 軽い「社内ツール」として、非エンジニアにデータ操作を任せる

外部公開しないインターナルツールとして十分使えるので、覚えておく価値があります。

## 3-2. 最小の登録

```python
# polls/admin.py
from django.contrib import admin
from .models import Question, Choice

admin.site.register(Question)
admin.site.register(Choice)
```

これだけで `/admin/` に Question と Choice が現れ、CRUD できます。ただし見た目は素朴 (`Question object (1)` のような表示)。

## 3-3. ModelAdmin で見た目を整える

```python
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["question_text", "pub_date", "was_published_recently"]
    list_filter = ["pub_date"]
    search_fields = ["question_text"]
    ordering = ["-pub_date"]
    list_per_page = 50
    date_hierarchy = "pub_date"
```

各オプションの意味:

| オプション | 効果 |
|---|---|
| `list_display` | 一覧画面に表示するカラム |
| `list_filter` | 右サイドバーにフィルタが出る |
| `search_fields` | 上部に検索ボックスが出る（部分一致 = `icontains`） |
| `ordering` | 一覧のデフォルト並び順 |
| `list_per_page` | 1 ページの件数 |
| `date_hierarchy` | 上部に「年→月→日」のドリルダウンが出る |

> `was_published_recently` のような **メソッド** も `list_display` に入れられます。Admin の標準機能だけでブール値の絵文字（◯/×）にもなります。

```python
@admin.display(boolean=True, description="最近公開？")
def was_published_recently(self, obj):
    return obj.was_published_recently()
```

## 3-4. fieldsets でフォームを整理

「タイトル系」と「公開日系」をブロック分けする:

```python
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ["question_text"]}),
        ("公開情報", {
            "fields": ["pub_date"],
            "classes": ["collapse"],          # 初期状態で折りたたむ
            "description": "公開日時を未来にすると予約公開になります",
        }),
    ]
```

## 3-5. Inline で関連モデルをまとめて編集

質問の編集画面に「選択肢」を埋め込みたい:

```python
class ChoiceInline(admin.TabularInline):     # 横並びテーブル形式
    model = Choice
    extra = 3                                # 空フォームを 3 行用意

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["question_text", "pub_date"]
    inlines = [ChoiceInline]
```

`StackedInline` だと縦に大きく展開、`TabularInline` だと表形式（コンパクト）。普通は `TabularInline` のほうが見やすいです。

## 3-6. `@admin.register` デコレータ

`admin.site.register(Model, ModelAdmin)` を書くより簡潔:

```python
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    ...
```

特別な理由がなければこちらを使います。

## ハンズオン③ Question / Choice の Admin

### 事前準備: スーパーユーザーを作る

```bash
uv run python manage.py createsuperuser
```

ユーザー名・メール・パスワードを聞かれるので入力。

### 1. polls/admin.py を以下に置き換える

```python
from django.contrib import admin
from .models import Choice, Question


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["question_text", "pub_date", "was_published_recently"]
    list_filter = ["pub_date"]
    search_fields = ["question_text"]
    date_hierarchy = "pub_date"
    fieldsets = [
        (None, {"fields": ["question_text"]}),
        ("公開情報", {
            "fields": ["pub_date"],
            "classes": ["collapse"],
        }),
    ]
    inlines = [ChoiceInline]


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ["choice_text", "question", "votes"]
    list_filter = ["question"]
    search_fields = ["choice_text"]
```

### 2. 動作確認

```bash
uv run python manage.py runserver
```

ブラウザで `http://127.0.0.1:8000/admin/` にアクセスし、作ったスーパーユーザーでログイン。

確認ポイント:
- 「Polls」セクションに「質問」「選択肢」が出ている
- 「質問を追加」を押すと、下部に選択肢のフォームが 3 行ある
- 一覧で `question_text`, `pub_date` のほか「最近公開？」列が見える
- 検索ボックスと右側のフィルタが効く

> Admin は実務でも本当に便利です。**「とりあえず Admin から登録できるようにしておけば、フロントが完成していなくてもデモできる」** のが大きい。

---

# 第4章 views.py — リクエストを処理する

## 4-1. ビュー関数のシグネチャ

```python
def my_view(request, *args, **kwargs):
    # request: HttpRequest オブジェクト
    # *args, **kwargs: URL からキャプチャされた値
    return HttpResponse(...)
```

URL パターンが `path("<int:question_id>/", views.detail)` なら、ビューには `question_id` がキーワード引数で渡ります。

## 4-2. render() ショートカット

「テンプレートを読んで → コンテキストを埋め込んで → HttpResponse にして返す」を 1 行で:

```python
from django.shortcuts import render

def index(request):
    questions = Question.objects.all()[:5]
    return render(request, "polls/index.html", {"latest_question_list": questions})
```

引数:
- 第1: `request`
- 第2: テンプレートのパス（`<app>/templates/<app>/<file>.html` の `<app>/<file>.html` 部分）
- 第3: テンプレートに渡すコンテキスト dict

## 4-3. get_object_or_404()

「ID で取って、なければ 404」を 1 行:

```python
from django.shortcuts import get_object_or_404

def detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, "polls/detail.html", {"question": question})
```

`Question.DoesNotExist` を自分で `try/except` する代わりに使う、定番ヘルパーです。

## 4-4. HttpResponseRedirect と reverse()

POST 後に他の URL に飛ばすときの定番:

```python
from django.http import HttpResponseRedirect
from django.urls import reverse

def vote(request, question_id):
    # ... 投票処理 ...
    return HttpResponseRedirect(reverse("polls:results", args=(question_id,)))
```

「**POST/Redirect/GET パターン**」と呼ばれる Web の定石。POST で更新 → 302 リダイレクト → GET で結果ページを表示。これによりブラウザの再読み込みで二重投稿が起きなくなります。

## 4-5. POST と CSRF

`<form method="post">` で送られた値は `request.POST` に dict 風に入っています:

```python
def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    selected_choice = question.choices.get(pk=request.POST["choice"])
    selected_choice.votes += 1
    selected_choice.save()
    return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))
```

POST フォームには **必ず `{% csrf_token %}` を入れる**（テンプレート側）。Django のミドルウェアが自動チェックするので、入れ忘れると 403。

## ハンズオン④ ビューを実装する

### polls/views.py を以下に置き換える

```python
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone

from .models import Choice, Question


def index(request):
    """直近に公開された質問を最大 5 件表示。"""
    latest_question_list = (
        Question.objects.filter(pub_date__lte=timezone.now())
        .order_by("-pub_date")[:5]
    )
    return render(
        request,
        "polls/index.html",
        {"latest_question_list": latest_question_list},
    )


def detail(request, question_id):
    """質問の詳細と投票フォーム。"""
    question = get_object_or_404(
        Question.objects.filter(pub_date__lte=timezone.now()),
        pk=question_id,
    )
    return render(request, "polls/detail.html", {"question": question})


def results(request, question_id):
    """投票結果。"""
    question = get_object_or_404(Question, pk=question_id)
    return render(request, "polls/results.html", {"question": question})


def vote(request, question_id):
    """投票を受け付ける。POST 専用想定。"""
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choices.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "選択肢を選んでください。",
            },
        )
    selected_choice.votes += 1
    selected_choice.save()
    return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))
```

ポイント:

- `index` と `detail` は **`pub_date__lte=timezone.now()`** で **未公開（未来日付）の質問は除外**。これは「予約投稿」を実現するためで、第6章のテストでこの挙動を担保します。
- `vote` で `question.choices.get(...)` を使えるのは、`Choice` の FK に `related_name="choices"` を付けたから（第1章ハンズオン）。
- `vote` は **POST のときだけ呼ばれる想定** なので、`request.POST["choice"]` が無い場合のエラー表示も用意してあります。

ブラウザで `/polls/` を開いてみると、テンプレートが無いので `TemplateDoesNotExist` のエラーになるはず。次章でテンプレートを作ります。

---

# 第5章 テンプレートを書く

## 5-1. テンプレートの置き場所

`settings.TEMPLATES` の `APP_DIRS=True` 設定により、各アプリの `templates/` 配下が自動で読まれます。**アプリ名で名前空間を切る** のがお作法:

```
polls/
  templates/
    polls/
      index.html
      detail.html
      results.html
```

`render(request, "polls/index.html", ...)` の文字列が、この `polls/templates/` 配下からの相対パスです。

## 5-2. 主要なタグ・フィルタ

| 構文 | 役割 |
|---|---|
| `{{ var }}` | 変数の出力（自動エスケープあり） |
| `{{ obj.attr }}` | 属性アクセス（メソッド・dict キー・リスト index も同じドット記法） |
| `{{ var|filter }}` | フィルタ（`{{ name|upper }}`、`{{ count|default:0 }}` など） |
| `{% if cond %}...{% endif %}` | 条件分岐 |
| `{% for x in xs %}...{% endfor %}` | ループ |
| `{% url 'polls:detail' question.id %}` | URL の逆引き |
| `{% csrf_token %}` | CSRF トークンを `<input>` として出力 |
| `{% block name %}...{% endblock %}` | ブロック（テンプレート継承） |
| `{% extends "base.html" %}` | 親テンプレートを継承 |
| `{% include "_partial.html" %}` | 部分テンプレートを差し込み |

## ハンズオン⑤ 4 つのテンプレートを作る

### 1. polls/templates/polls/index.html

```html
{% if latest_question_list %}
  <ul>
    {% for question in latest_question_list %}
      <li>
        <a href="{% url 'polls:detail' question.id %}">{{ question.question_text }}</a>
      </li>
    {% endfor %}
  </ul>
{% else %}
  <p>まだ質問はありません。</p>
{% endif %}
```

### 2. polls/templates/polls/detail.html

```html
<h1>{{ question.question_text }}</h1>

{% if error_message %}<p><strong>{{ error_message }}</strong></p>{% endif %}

<form action="{% url 'polls:vote' question.id %}" method="post">
  {% csrf_token %}
  {% for choice in question.choices.all %}
    <label>
      <input type="radio" name="choice" value="{{ choice.id }}">
      {{ choice.choice_text }}
    </label><br>
  {% endfor %}
  <button type="submit">投票</button>
</form>
```

### 3. polls/templates/polls/results.html

```html
<h1>{{ question.question_text }}</h1>

<ul>
  {% for choice in question.choices.all %}
    <li>{{ choice.choice_text }} — {{ choice.votes }} 票</li>
  {% endfor %}
</ul>

<a href="{% url 'polls:detail' question.id %}">もう一度投票する</a>
```

### 4. 動作確認

`runserver` を起動して、以下を試す:

1. `/admin/` で「質問」を 1 件追加（公開日時は **過去日時**）。選択肢も 2-3 個登録。
2. `/polls/` で一覧に出ていることを確認。
3. リンクから詳細へ → ラジオで選択 → 投票 → results へ自動リダイレクト。
4. `/admin/` で公開日時を **未来日時** にすると、`/polls/` の一覧から消えることを確認。

ここまでできたら投票アプリは「動く」状態です。次章でテストを書きます。

---

# 第6章 tests.py — 自動テストで安心して育てる

## 6-1. なぜテストを書くか

未来の自分・チームメイトを助けるためです。具体的には:

- **手動確認の時間を削る** — 機能が増えるほど手動回帰は破綻する
- **意図をコードで残す** — 「未公開の質問は出ないはず」をテストにすれば仕様書代わり
- **改修時の安心** — 関連コードを直しても壊れなければグリーンのまま
- **バグの再発防止** — バグを直すときは **先に再現テスト** を書く

## 6-2. TestCase の基本

```python
from django.test import TestCase

class QuestionModelTests(TestCase):
    def test_xxx(self):
        # 各 test_* メソッドが独立したテスト
        # メソッドごとに DB はリセットされる
        ...
```

ルール:

- ファイル名は `tests.py`（または `tests/test_*.py`）
- クラスは `django.test.TestCase` を継承
- テストメソッドは **`test_` で始める**
- メソッド名は **何が起きるはずか** を説明的に書く（例: `test_returns_404_when_question_is_in_future`）

## 6-3. アサーション早見表

| メソッド | 意味 |
|---|---|
| `assertEqual(a, b)` | `a == b` |
| `assertTrue(x)` / `assertFalse(x)` | 真/偽 |
| `assertIs(a, b)` | `a is b`（恒等性） |
| `assertIn(item, container)` | `item in container` |
| `assertContains(response, text)` | レスポンス HTML に文字列が含まれる |
| `assertNotContains(response, text)` | 含まれない |
| `assertRedirects(response, url)` | 302 リダイレクト先を検証 |
| `assertQuerySetEqual(qs, [...])` | クエリセットの中身が一致 |

## 6-4. self.client でビューをテスト

`TestCase` には **本物のブラウザ無しで HTTP リクエストを送れる `self.client`** が付属:

```python
from django.urls import reverse

class IndexViewTests(TestCase):
    def test_returns_200(self):
        response = self.client.get(reverse("polls:index"))
        self.assertEqual(response.status_code, 200)
```

`self.client.post(url, data)` で POST も送れます。

## 6-5. setUp で共通データを準備

```python
class QuestionDetailTests(TestCase):
    def setUp(self):
        # 各テストメソッドの前に呼ばれる
        self.question = Question.objects.create(
            question_text="共通の質問",
            pub_date=timezone.now() - timedelta(days=1),
        )
```

データ準備が長いとき重宝します。

## 6-6. テスト用ヘルパー関数

「過去/未来の質問を作る」は何度も出てくるので関数化しておくと便利:

```python
def create_question(question_text: str, days: int) -> Question:
    """`days` 日後（負なら前）に公開される質問を作って返す。"""
    return Question.objects.create(
        question_text=question_text,
        pub_date=timezone.now() + timedelta(days=days),
    )
```

## ハンズオン⑥ Question.was_published_recently のテスト

### polls/tests.py を以下に置き換える

```python
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Question


def create_question(question_text: str, days: int) -> Question:
    """days 日後（負なら過去）の公開日時で質問を作成。"""
    return Question.objects.create(
        question_text=question_text,
        pub_date=timezone.now() + timedelta(days=days),
    )


class QuestionModelTests(TestCase):
    def test_was_published_recently_with_future_question(self):
        future_question = Question(pub_date=timezone.now() + timedelta(days=30))
        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        old_question = Question(pub_date=timezone.now() - timedelta(days=1, seconds=1))
        self.assertIs(old_question.was_published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        recent = Question(pub_date=timezone.now() - timedelta(hours=23, minutes=59))
        self.assertIs(recent.was_published_recently(), True)
```

### 実行

```bash
uv run python manage.py test polls
```

`Ran 3 tests in 0.00Xs / OK` になれば成功。

## ハンズオン⑦ ビューのテスト

`polls/tests.py` の末尾に追記:

```python
class QuestionIndexViewTests(TestCase):
    def test_no_questions(self):
        response = self.client.get(reverse("polls:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "まだ質問はありません。")
        self.assertQuerySetEqual(response.context["latest_question_list"], [])

    def test_past_question_is_displayed(self):
        question = create_question("過去の質問", days=-1)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(response.context["latest_question_list"], [question])

    def test_future_question_is_not_displayed(self):
        create_question("未来の質問", days=1)
        response = self.client.get(reverse("polls:index"))
        self.assertContains(response, "まだ質問はありません。")
        self.assertQuerySetEqual(response.context["latest_question_list"], [])

    def test_only_past_when_both_exist(self):
        past = create_question("過去", days=-1)
        create_question("未来", days=1)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(response.context["latest_question_list"], [past])


class QuestionDetailViewTests(TestCase):
    def test_future_question_returns_404(self):
        future = create_question("未来", days=5)
        response = self.client.get(reverse("polls:detail", args=(future.id,)))
        self.assertEqual(response.status_code, 404)

    def test_past_question_is_displayed(self):
        past = create_question("過去", days=-1)
        response = self.client.get(reverse("polls:detail", args=(past.id,)))
        self.assertContains(response, past.question_text)
```

### 実行

```bash
uv run python manage.py test polls
```

`Ran 9 tests in 0.0XXs / OK` になれば、polls アプリは **テスト付きで完成** です。

## 6-7. テスト DB について

- `manage.py test` は **専用のテスト DB** を作って使い、終わると消します
- なので、本物の `django_dev` データは触らない
- 各 `test_` メソッドの前後で **トランザクション ROLLBACK** が走るので、テスト間でデータは持ち越さない
- `setUpTestData` (クラスメソッド) を使うと「クラス内全テストで共有する初期データ」を 1 回だけ作れて速くなる

```python
class HeavyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.question = create_question("共通", days=-1)
```

## 6-8. テスト時の Tips

- **失敗をすぐ表示**: `--failfast` で 1 件失敗で止める
- **並列**: `--parallel auto` で CPU 並列。テストが多い時に効く
- **特定だけ**: `uv run python manage.py test polls.tests.QuestionModelTests`
- **カバレッジ計測**: `coverage run --source=polls manage.py test && coverage report` (`uv add coverage` が必要)

---

# 第7章 urls.py の総まとめ

`docs/01-...` で詳しくやっているので、ここはダイジェスト + 実務 Tips のみ。

## 7-1. 階層構造のおさらい

```
config/urls.py            # プロジェクトの目次
└── polls/urls.py         # アプリ単位の目次（app_name="polls"）
    ├── index             → polls:index
    ├── detail            → polls:detail
    ├── results           → polls:results
    └── vote              → polls:vote
```

`config/urls.py`:

```python
urlpatterns = [
    path("admin/", admin.site.urls),
    path("polls/", include("polls.urls")),
    path("", include("todo.urls")),
]
```

`polls/urls.py`:

```python
app_name = "polls"

question_patterns = [
    path("", views.detail, name="detail"),
    path("results/", views.results, name="results"),
    path("vote/", views.vote, name="vote"),
]

urlpatterns = [
    path("", views.index, name="index"),
    path("<int:question_id>/", include(question_patterns)),
]
```

## 7-2. URL 設計のコツ（実務）

- **末尾スラッシュ統一** (`/polls/`)。Django のデフォルトに合わせる
- **複数形 + ID** (`/polls/5/`、`/users/42/`) — REST の慣習
- **動詞より名詞** (`/polls/5/vote/` も OK だが、本物の API なら `POST /polls/5/votes` のような名詞ベースが良い)
- **API と画面で URL を分ける** (`/api/v1/polls/` と `/polls/` を別の include で分離)
- **公開 URL に内部 ID を出さないことも検討** (`/polls/<slug>/`、`/users/<username>/`)

## 7-3. デバッグ術

```bash
# 全 URL を一覧（django-extensions）
uv run python manage.py show_urls

# 名前から URL を逆引き
uv run python manage.py shell -c "from django.urls import reverse; print(reverse('polls:detail', args=(1,)))"

# 実際のリクエストで動作確認
curl -i http://127.0.0.1:8000/polls/1/
```

---

# チートシート

## モデルフィールド

```
CharField(max_length=N)        BooleanField
TextField                      DateField / DateTimeField
IntegerField                   DecimalField(max_digits, decimal_places)
EmailField / URLField          SlugField
ForeignKey(M, on_delete=...)   ManyToManyField(M)
                               OneToOneField(M, on_delete=...)
```

## マイグレーション

```bash
uv run python manage.py makemigrations [APP]              # 設計図作成
uv run python manage.py makemigrations --empty APP        # 空（データマイグレーション用）
uv run python manage.py sqlmigrate APP NUMBER             # SQL 確認
uv run python manage.py migrate [APP] [NUMBER]            # 適用 / 戻し
uv run python manage.py migrate APP zero                  # アプリのテーブル全消し
uv run python manage.py showmigrations [APP]              # 状態確認
uv run python manage.py squashmigrations APP NUMBER       # 統合
```

## Admin

```python
@admin.register(Model)
class ModelAdmin(admin.ModelAdmin):
    list_display = [...]            # 一覧カラム
    list_filter = [...]             # 右サイドバー
    search_fields = [...]           # 検索ボックス
    ordering = [...]                # デフォルト並び
    date_hierarchy = "field"        # 日付ドリルダウン
    fieldsets = [...]               # フォームのブロック分け
    inlines = [...]                 # 関連モデル埋め込み
    readonly_fields = [...]         # 読み取り専用
    autocomplete_fields = [...]     # FK の検索フィールド化
```

## ビュー

```python
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse

render(request, "app/template.html", {"key": value})
get_object_or_404(Model, pk=id)
HttpResponseRedirect(reverse("app:name", args=(arg,)))
redirect("app:name", arg)        # ↑ の短縮形
```

## テスト

```python
from django.test import TestCase
from django.urls import reverse

class XxxTests(TestCase):
    @classmethod
    def setUpTestData(cls): ...
    def setUp(self): ...

    def test_yyy(self):
        response = self.client.get(reverse("app:name"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "expected text")
        self.assertQuerySetEqual(response.context["key"], [...])
```

```bash
uv run python manage.py test [APP[.TestClass[.test_method]]]
uv run python manage.py test --failfast --parallel auto
```

---

# まとめ

ハンズオン①〜⑦を完走したなら、polls はこんな状態のはずです:

- [x] Question / Choice モデルが定義されている
- [x] マイグレーションが作られて DB に反映されている
- [x] Admin でデータを CRUD できる（Inline 付き）
- [x] index / detail / results / vote のリアルなビューが動く
- [x] テンプレートで一覧・詳細・投票・結果を表示できる
- [x] 9 件のテストがグリーン

次に学ぶと良いトピック:

- **クラスベースビュー** (`ListView`, `DetailView`) — 同じ機能をもっと短く書く
- **フォーム** (`forms.py`, `ModelForm`) — POST のバリデーションを構造化
- **認証** (`django.contrib.auth`) — ログイン/サインアップ/権限
- **静的ファイル & デプロイ** — `collectstatic`, gunicorn, nginx
- **Django REST Framework** — JSON API を作る

これらは別ドキュメントで扱います。

---

# 補足: 各章の自己チェック

各章を読み終えたら、この問いに即答できるか確認してください。詰まったらその章を読み直すサイン。

**第1章 (models)**
- `null=True` と `blank=True` の違いは？
- `on_delete=CASCADE` と `PROTECT` の使い分けは？
- `__str__` を書く理由は？

**第2章 (migrations)**
- `makemigrations` と `migrate` のどちらが DB を変える？
- マイグレーションファイルはコミットすべき？理由は？
- `sqlmigrate` を本番反映前に使う理由は？

**第3章 (admin)**
- `list_display` と `list_filter` の違いは？
- `TabularInline` を使う典型シーンは？
- `@admin.register` のメリットは？

**第4章 (views)**
- `get_object_or_404` を使う理由は？
- POST/Redirect/GET パターンとは？
- `{% csrf_token %}` を入れ忘れるとどうなる？

**第5章 (templates)**
- なぜテンプレートを `polls/templates/polls/...` のように二重ネストする？
- `{% url 'polls:detail' q.id %}` と `/polls/{{q.id}}/` の違いは？

**第6章 (tests)**
- なぜ `setUpTestData` のほうが `setUp` より速いことがある？
- `assertQuerySetEqual` を使う場面は？
- バグ修正で「先に再現テスト」を書く理由は？
