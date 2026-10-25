from django.contrib import admin

from .models import Cart, CartItem, Inventory, Product, ProductImage

# データを見るための窓（見た目の調整はしない）
admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(Inventory)
admin.site.register(Cart)
admin.site.register(CartItem)
