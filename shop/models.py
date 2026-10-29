from django.conf import settings
from django.db import models
from django.db.models import Q

from blog.models import Category


class Product(models.Model):
    name = models.CharField(max_length=100)
    # お金は小数の誤差が出ない DecimalField。全体で10桁、そのうち小数点以下が2桁
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # 多対一: 第2部のカテゴリを使い回す。商品が残っているカテゴリは消せない
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # 価格は0以上。破ろうとすると、DB が保存を断る
            models.CheckConstraint(condition=Q(price__gte=0), name="shop_product_price_gte_0"),
        ]

    def __str__(self) -> str:
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")

    def __str__(self) -> str:
        return self.image.name


class Inventory(models.Model):
    # 一対一: 1つの商品に、在庫の行は1つ
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="inventory")
    quantity = models.IntegerField(default=0)  # 在庫の数

    class Meta:
        constraints = [
            # 在庫は0以上。マイナスの在庫は、DB が保存を断る
            models.CheckConstraint(
                condition=Q(quantity__gte=0), name="shop_inventory_quantity_gte_0"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product.name}: {self.quantity}"


class Cart(models.Model):
    # 一対一: 1人に、カートは1つ
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user_id} のカート"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()  # カートに入れた数

    class Meta:
        constraints = [
            # 同じカートに、同じ商品の行は1つだけ（2回入れたら数を足す）
            models.UniqueConstraint(
                fields=["cart", "product"], name="shop_cartitem_unique_cart_product"
            ),
            # 数は1以上
            models.CheckConstraint(
                condition=Q(quantity__gte=1), name="shop_cartitem_quantity_gte_1"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product.name} x {self.quantity}"


class Order(models.Model):
    class Status(models.TextChoices):
        # 名前 = "台帳に入る値", "人が読む名前"
        PLACED = "placed", "確定"
        SHIPPED = "shipped", "発送済み"
        COMPLETED = "completed", "完了"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    total = models.DecimalField(max_digits=12, decimal_places=2)  # 合計金額（確定した時点）
    # 注文の状態。選べる値は Status の3つ。作ったときは「確定」
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLACED)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"注文 {self.id}"

    def change_status(self, new_status: str) -> None:
        # 進んでよいのは「確定 → 発送済み → 完了」の順だけ（今の状態: 次に進める状態）
        next_status: dict[str, str] = {
            Order.Status.PLACED: Order.Status.SHIPPED,
            Order.Status.SHIPPED: Order.Status.COMPLETED,
        }
        if next_status.get(self.status) != new_status:
            new_label = Order.Status(new_status).label
            raise ValueError(f"「{self.get_status_display()}」から「{new_label}」には進めません")
        self.status = new_status
        self.save(update_fields=["status"])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    # 注文の記録が残っている商品は消せない
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    # 買った時点の価格を写しておく。あとで商品の価格が変わっても、注文の金額は変わらない
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()

    def __str__(self) -> str:
        return f"{self.product.name} x {self.quantity}"
