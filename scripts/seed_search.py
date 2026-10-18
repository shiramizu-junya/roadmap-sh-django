# 第2部-11（検索と絞り込み）を試すための記事を入れる。
# 使い方: uv run python manage.py shell < scripts/seed_search.py
# 同じタイトルの記事があれば作らないので、何回流しても増えない。
from accounts.models import User
from blog.models import Category, Post, Tag

me = User.objects.get(username="shiramizu")
# carol がいなければ作る（パスワードは pass1234。ログインして 403 を試すとき用）
carol = User.objects.filter(username="carol").first() or User.objects.create_user(
    username="carol", password="pass1234"
)

programming, _ = Category.objects.get_or_create(name="プログラミング")
life, _ = Category.objects.get_or_create(name="生活")
travel, _ = Category.objects.get_or_create(name="旅行")

python, _ = Tag.objects.get_or_create(name="python")
django, _ = Tag.objects.get_or_create(name="django")
ninja, _ = Tag.objects.get_or_create(name="ninja")

# (タイトル, 本文, カテゴリ, 書いた人, タグ)。行末のコメントは、試してほしい検索
POSTS = [
    # --- プログラミング ---
    (
        "Django のモデル入門",
        "ForeignKey と ManyToManyField の違いをまとめた。",
        programming,
        me,
        [python, django],
    ),  # ?q=django
    (
        "DJANGO の管理画面を使ってみた",
        "データを目で確かめる窓として便利。",
        programming,
        me,
        [django],
    ),  # ?q=django（大文字でも当たる）
    (
        "Ninja でログイン API を作る",
        "JWT の身分証を返す。django-ninja-jwt を使った。",
        programming,
        me,
        [ninja],
    ),  # ?q=ninja（タイトル）
    (
        "型ヒントのメモ",
        "mypy が Ninja のスキーマも見てくれる。",
        programming,
        me,
        [python, ninja],
    ),  # ?q=ninja（本文だけ）
    (
        "ｄｊａｎｇｏ と全角で書いた記事",
        "全角の英字でも検索に当たるか試す。",
        programming,
        me,
        [],
    ),  # ?q=django（全角も当たる）
    (
        "SQL を数える",
        "N+1 問題は prefetch_related で直す。",
        programming,
        me,
        [django],
    ),  # ?q=prefetch
    (
        "進捗 100% 達成",
        "第2部の半分まで来た。",
        programming,
        me,
        [],
    ),  # q=100%（--data-urlencode で送る）
    # --- 生活 ---
    (
        "今日の日記",
        "朝から Django の勉強をした。",
        life,
        me,
        [],
    ),  # ?q=django&category_id=<生活の id>
    ("はは の誕生日", "ケーキを買った。", life, me, []),  # q=はは（パパ も当たる）
    ("パパ と散歩", "公園まで歩いた。", life, me, []),  # q=ぱぱ
    (
        "カフェで作業",
        "Ninja の公式ドキュメントを読んだ。",
        life,
        carol,
        [ninja],
    ),  # ?q=ninja&category_id=<生活の id>
    (
        "コーヒーの淹れ方",
        "豆は中挽き。お湯は 90 度くらい。",
        life,
        carol,
        [],
    ),  # どの検索にも当たらない
    # --- 旅行 ---
    (
        "京都旅行",
        "お寺を回った。電車で Django の本を読んだ。",
        travel,
        me,
        [],
    ),  # ?q=django&category_id=<旅行の id>
    ("北海道でキャンプ", "星がきれいだった。", travel, carol, []),  # ?category_id=<旅行の id>
    ("旅の持ち物リスト", "ノート PC と充電器。", travel, carol, []),  # ?category_id=<旅行の id>
]

created = 0
for title, body, category, author, tags in POSTS:
    post, is_new = Post.objects.get_or_create(
        title=title, defaults={"body": body, "category": category, "author": author}
    )
    if is_new:
        post.tags.set(tags)
        created += 1

print(f"記事を {created} 件作りました（全部で {Post.objects.count()} 件）")
print("カテゴリの id:", {c.name: c.id for c in Category.objects.all()})
