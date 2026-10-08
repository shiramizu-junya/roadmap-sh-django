from django.contrib import admin
from django.urls import path

from blog import views
from config.api import api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("manual/posts/", views.post_list),  # 1-5・1-6 の手書き版（比較用に残す）
    path("api/", api.urls),  # Ninja の API 一式
]
