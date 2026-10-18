from django.contrib import admin

from .models import Category, Comment, Post, Tag

# Post を管理画面に出す（見た目の調整はしない）
admin.site.register(Post)
admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(Comment)
