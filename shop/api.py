from datetime import datetime
from decimal import Decimal

from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Avg, Count, F
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Field, Router, Schema, Status
from ninja.errors import HttpError
from ninja_jwt.authentication import JWTAuth

from .models import Cart, CartItem, Inventory, Order, OrderItem, Product, Review

# 商品の API 一式。URL の頭（/products）は config/api.py で決める
router = Router()


class ProductOut(Schema):
    id: int
    name: str
    price: Decimal  # 金額。JSON では "1200.00" のような文字列になる
    category_id: int
    stock: int = Field(alias="inventory.quantity")  # 在庫の数（一対一の先をたどる）
    review_count: int  # レビューの件数（annotate で付け足した値）
    rating_avg: float | None  # 星の平均。レビューが無ければ null


def products_with_rating():
    # 在庫は JOIN で取り、レビューの件数と星の平均は MySQL に数えさせて、商品ごとに付け足す
    return Product.objects.select_related("inventory").annotate(
        review_count=Count("reviews"), rating_avg=Avg("reviews__rating")
    )


@router.get("", response=list[ProductOut])
def list_products(request: HttpRequest):
    return products_with_rating().order_by("id")


@router.get("/{product_id}", response=ProductOut)
def get_product(request: HttpRequest, product_id: int):
    return get_object_or_404(products_with_rating(), id=product_id)


class ReviewIn(Schema):
    rating: int = Field(ge=1, le=5)  # 星は1〜5。外れたら 422
    comment: str = ""


class ReviewOut(Schema):
    id: int
    product_id: int
    user_id: int
    rating: int
    comment: str


@router.post("/{product_id}/reviews", response={201: ReviewOut}, auth=JWTAuth())
def create_review(request: HttpRequest, product_id: int, payload: ReviewIn):
    product = get_object_or_404(Product, id=product_id)
    assert request.user.is_authenticated
    if Review.objects.filter(product=product, user=request.user).exists():
        raise HttpError(409, "この商品には、もうレビューを書いています")
    review = Review.objects.create(
        product=product, user=request.user, rating=payload.rating, comment=payload.comment
    )
    return Status(201, review)


# カートの API 一式。URL の頭（/cart）は config/api.py で決める
cart_router = Router()


class CartItemIn(Schema):
    product_id: int
    quantity: int = Field(default=1, ge=1)  # 省略したら1個。0以下は 422


class CartItemOut(Schema):
    product_id: int
    name: str = Field(alias="product.name")
    price: Decimal = Field(alias="product.price")
    quantity: int


class CartOut(Schema):
    items: list[CartItemOut]
    total: Decimal  # 合計金額


@cart_router.post("/items", response={201: CartItemOut}, auth=JWTAuth())
def add_to_cart(request: HttpRequest, payload: CartItemIn):
    product = get_object_or_404(Product, id=payload.product_id)
    assert request.user.is_authenticated
    # 自分のカートを取る。無ければ作る
    cart, _ = Cart.objects.get_or_create(user=request.user)
    # 同じ商品の行を取る。無ければ、入れた数で作る
    item, created = CartItem.objects.get_or_create(
        cart=cart, product=product, defaults={"quantity": payload.quantity}
    )
    if not created:
        # もう入っていたら、行は増やさずに数を足す。足し算は MySQL にさせる
        CartItem.objects.filter(id=item.id).update(quantity=F("quantity") + payload.quantity)
        item = CartItem.objects.get(id=item.id)  # 足したあとの数を読み直す

    return Status(201, item)


@cart_router.get("", response=CartOut, auth=JWTAuth())
def get_cart(request: HttpRequest):
    assert request.user.is_authenticated
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related("product").order_by("id")
    total = sum((item.product.price * item.quantity for item in items), Decimal("0"))
    return {"items": items, "total": total}


# 注文の API 一式。URL の頭（/orders）は config/api.py で決める
order_router = Router()


class OrderItemOut(Schema):
    product_id: int
    price: Decimal  # 買った時点の価格
    quantity: int


class OrderOut(Schema):
    id: int
    total: Decimal
    created_at: datetime
    items: list[OrderItemOut]
    status: Order.Status  # "placed" / "shipped" / "completed" のどれか


@order_router.post("", response={201: OrderOut}, auth=JWTAuth())
def place_order(request: HttpRequest):
    assert request.user.is_authenticated
    # ここから下は「全部やるか、何もしないか」。途中で例外が出たら、全部取り消す
    with transaction.atomic():
        # カートの行に鍵をかけて読む。同じカートの2つ目の注文は、1つ目が終わるまでここで待つ
        cart = get_object_or_404(Cart.objects.select_for_update(), user=request.user)
        cart_items = list(cart.items.select_related("product"))
        if not cart_items:
            raise HttpError(400, "カートが空です")

        total = sum((ci.product.price * ci.quantity for ci in cart_items), Decimal("0"))
        order = Order.objects.create(user=request.user, total=total)

        email = request.user.email
        if email:
            # 確認メールは、注文が確定（COMMIT）したあとに送る。取り消されたら送らない
            transaction.on_commit(
                lambda: send_mail(
                    subject=f"注文 {order.id} を受け付けました",
                    message=f"合計 {total} 円",
                    from_email=None,
                    recipient_list=[email],
                )
            )

        # 注文の明細を、INSERT 1本でまとめて作る
        OrderItem.objects.bulk_create(
            [
                OrderItem(
                    order=order, product=ci.product, price=ci.product.price, quantity=ci.quantity
                )
                for ci in cart_items
            ]
        )
        for ci in cart_items:
            # 在庫が足りているときだけ減らす。比べるのも引くのも、MySQL が UPDATE 1本の中でやる
            updated = Inventory.objects.filter(
                product=ci.product, quantity__gte=ci.quantity
            ).update(quantity=F("quantity") - ci.quantity)
            if updated == 0:
                # 例外で with を抜けると、上で作った注文と明細も無かったことになる
                raise HttpError(409, f"「{ci.product.name}」の在庫が足りません")

        cart.items.all().delete()  # カートを空にする

    return Status(201, order)


class OrderStatusIn(Schema):
    status: Order.Status  # 3つ以外の値は 422


@order_router.patch("/{order_id}/status", response=OrderOut, auth=JWTAuth())
def change_order_status(request: HttpRequest, order_id: int, payload: OrderStatusIn):
    # 状態を進めるのはお店の人だけ（管理画面に入れるスタッフ）
    if not request.user.is_staff:
        raise HttpError(403, "お店の人しか変えられません")
    order = get_object_or_404(Order, id=order_id)
    try:
        order.change_status(payload.status)  # 進んでよいかは、モデルが決める
    except ValueError as e:
        raise HttpError(409, str(e)) from e
    return order
