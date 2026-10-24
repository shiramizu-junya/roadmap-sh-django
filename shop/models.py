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
