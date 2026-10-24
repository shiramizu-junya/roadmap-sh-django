from ninja import NinjaAPI

from accounts.api import router as auth_router
from blog.api import router as posts_router
from shop.api import router as products_router

api = NinjaAPI()

# アプリごとの Router を、URL の頭を決めて差し込む
api.add_router("/posts", posts_router, tags=["posts"])
api.add_router("/auth", auth_router, tags=["auth"])
api.add_router("/products", products_router, tags=["products"])
