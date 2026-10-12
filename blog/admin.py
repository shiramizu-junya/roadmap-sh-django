from django.contrib import admin

from .models import Category, Post

# Post を管理画面に出す（見た目の調整はしない）
admin.site.register(Post)
admin.site.register(Category)
