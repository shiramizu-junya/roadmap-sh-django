# ローカルの DB に、試すためのデータを入れる。
# - ブログ: 第2部-11（検索と絞り込み）を試すための記事
# - ショップ: 第4部（React の画面）を試すための商品・在庫・レビュー・注文
# 使い方: SQL_LOG=0 uv run python manage.py shell < scripts/seed.py
# 同じタイトルの記事・同じ名前の商品・同じ人のレビューがあれば作らないので、何回流しても増えない。
from decimal import Decimal

from django.db import transaction

from accounts.models import User
from blog.models import Category, Post, Tag
from shop.models import Inventory, Order, OrderItem, Product, Review

# 記事・レビュー・注文を書く人。いなければ作る（パスワードは pass1234。ログインして試すとき用）
me = User.objects.get(username="shiramizu")
users = {"shiramizu": me}
for name in ["carol", "dave", "erin"]:
    users[name] = User.objects.filter(username=name).first() or User.objects.create_user(
        username=name, password="pass1234"
    )
carol = users["carol"]

categories = {
    name: Category.objects.get_or_create(name=name)[0]
    for name in ["プログラミング", "生活", "旅行", "漫画", "家電"]
}
programming = categories["プログラミング"]
life = categories["生活"]
travel = categories["旅行"]

python, _ = Tag.objects.get_or_create(name="python")
django, _ = Tag.objects.get_or_create(name="django")
ninja, _ = Tag.objects.get_or_create(name="ninja")

# ===== ブログ =====

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


# ===== ショップ =====

# (商品名, 価格, カテゴリ, 在庫)。在庫 0 は「売り切れ」の表示を試す用
PRODUCTS = [
    ("Django 入門", "2980.00", "プログラミング", 15),
    ("Python ノート", "450.50", "プログラミング", 0),
    ("TypeScript 実践ガイド", "3520.00", "プログラミング", 8),
    ("SQL 図鑑", "2200.00", "プログラミング", 3),
    ("ステンレスマグカップ", "1650.00", "生活", 40),
    ("今治タオル 2枚組", "2400.00", "生活", 25),
    ("アロマキャンドル", "980.00", "生活", 0),
    ("京都ガイドブック", "1320.00", "旅行", 12),
    ("トラベル枕", "1890.00", "旅行", 6),
    ("冒険マンガ 1巻", "528.00", "漫画", 100),
    ("冒険マンガ 2巻", "528.00", "漫画", 1),
    ("ワイヤレスイヤホン", "12800.00", "家電", 5),
    ("USB-C 充電器 65W", "4980.00", "家電", 20),
    ("モバイルバッテリー", "3980.00", "家電", 0),
]

# (商品名, 書いた人, 星, 感想)。レビューが無い商品も残して、rating_avg の null を試せるようにする
REVIEWS = [
    ("Django 入門", "carol", 5, "図が多くて分かりやすい。"),
    ("Django 入門", "dave", 4, "後半の ORM の章が良かった。"),
    ("Django 入門", "erin", 4, ""),
    ("Python ノート", "carol", 3, "薄いけど手元に置くには便利。"),
    ("TypeScript 実践ガイド", "dave", 5, "型の付け方がよく分かった。"),
    ("ステンレスマグカップ", "erin", 4, "保温が長持ちする。"),
    ("ステンレスマグカップ", "carol", 2, "少し重い。"),
    ("今治タオル 2枚組", "dave", 5, "ふわふわ。"),
    ("京都ガイドブック", "shiramizu", 4, "地図が見やすい。"),
    ("冒険マンガ 1巻", "carol", 5, "続きが気になる！"),
    ("冒険マンガ 1巻", "dave", 5, ""),
    ("冒険マンガ 1巻", "erin", 3, "絵は好き。"),
    ("ワイヤレスイヤホン", "erin", 1, "すぐ片方が聞こえなくなった。"),
    ("ワイヤレスイヤホン", "dave", 4, "音は良い。"),
]

# (注文した人, 状態, [(商品名, 数)])。履歴の画面と、状態の表示を試す用
ORDERS = [
    ("carol", Order.Status.COMPLETED, [("Django 入門", 1), ("冒険マンガ 1巻", 2)]),
    ("carol", Order.Status.SHIPPED, [("ステンレスマグカップ", 1)]),
    ("carol", Order.Status.PLACED, [("USB-C 充電器 65W", 1), ("SQL 図鑑", 1)]),
    ("dave", Order.Status.COMPLETED, [("今治タオル 2枚組", 2)]),
    ("dave", Order.Status.PLACED, [("TypeScript 実践ガイド", 1)]),
    ("erin", Order.Status.SHIPPED, [("ワイヤレスイヤホン", 1), ("冒険マンガ 1巻", 1)]),
]

with transaction.atomic():
    created_posts = 0
    for title, body, category, author, tags in POSTS:
        post, is_new = Post.objects.get_or_create(
            title=title, defaults={"body": body, "category": category, "author": author}
        )
        if is_new:
            post.tags.set(tags)
            created_posts += 1

    products = {}
    created_products = 0
    for name, price, category_name, stock in PRODUCTS:
        product, is_new = Product.objects.get_or_create(
            name=name, defaults={"price": Decimal(price), "category": categories[category_name]}
        )
        Inventory.objects.get_or_create(product=product, defaults={"quantity": stock})
        products[name] = product
        created_products += is_new

    created_reviews = 0
    for product_name, user_name, rating, comment in REVIEWS:
        _review, is_new = Review.objects.get_or_create(
            product=products[product_name],
            user=users[user_name],
            defaults={"rating": rating, "comment": comment},
        )
        created_reviews += is_new

    # 注文は「同じ商品名」のような目印が無いので、seed の人にまだ注文が無いときだけ作る
    created_orders = 0
    seed_buyers = [users[name] for name in ["carol", "dave", "erin"]]
    if not Order.objects.filter(user__in=seed_buyers).exists():
        for user_name, status, lines in ORDERS:
            total = sum((products[name].price * quantity for name, quantity in lines), Decimal("0"))
            order = Order.objects.create(user=users[user_name], total=total, status=status)
            OrderItem.objects.bulk_create(
                [
                    OrderItem(
                        order=order,
                        product=products[name],
                        price=products[name].price,
                        quantity=quantity,
                    )
                    for name, quantity in lines
                ]
            )
            created_orders += 1

print(f"記事を {created_posts} 件作りました（全部で {Post.objects.count()} 件）")
print(f"商品を {created_products} 件作りました（全部で {Product.objects.count()} 件）")
print(f"レビューを {created_reviews} 件作りました（全部で {Review.objects.count()} 件）")
print(f"注文を {created_orders} 件作りました（全部で {Order.objects.count()} 件）")
print("カテゴリの id:", {c.name: c.id for c in Category.objects.all()})
print("ログインして試せる人（パスワード pass1234）: carol / dave / erin")
