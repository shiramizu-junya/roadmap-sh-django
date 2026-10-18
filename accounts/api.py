from django.contrib.auth import authenticate
from django.http import HttpRequest
from django.shortcuts import get_object_or_404  # 追加
from ninja import Field, Router, Schema, Status  # Field を追加
from ninja_jwt.authentication import JWTAuth  # 追加
from ninja_jwt.exceptions import TokenError
from ninja_jwt.tokens import RefreshToken

from .models import Profile, User  # 追加

# ログインまわりの API 一式。URL の頭（/auth）は config/api.py で決める
router = Router()


class LoginIn(Schema):
    username: str
    password: str


class TokenOut(Schema):
    access: str  # 身分証。API を呼ぶたびに見せる（有効期限が短い）
    refresh: str  # 身分証の引換券。access が切れたら新しいものと交換する


class RefreshIn(Schema):
    refresh: str


class AccessOut(Schema):
    access: str


class ErrorOut(Schema):
    detail: str


@router.post("/login", response={200: TokenOut, 401: ErrorOut})
def login(request: HttpRequest, payload: LoginIn):
    # ユーザー名とパスワードが合えば User、合わなければ None が返る
    user = authenticate(request, username=payload.username, password=payload.password)
    if user is None:
        return Status(401, {"detail": "ユーザー名かパスワードが違います"})
    # 引換券を作る（中に user_id が入る）
    # ignore: ライブラリの型注釈の誤り（cls: T）で mypy が怒るのを黙らせる。動きは正しい
    refresh = RefreshToken.for_user(user)  # type: ignore[misc]
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


@router.post("/refresh", response={200: AccessOut, 401: ErrorOut})
def refresh(request: HttpRequest, payload: RefreshIn):
    try:
        token = RefreshToken(payload.refresh)  # 署名と有効期限をここで確かめる
    except TokenError:
        return Status(401, {"detail": "引換券が無効か、期限切れです"})
    return {"access": str(token.access_token)}


class RegisterIn(Schema):
    username: str = Field(min_length=1, max_length=150)
    password: str = Field(min_length=8)  # 短すぎるパスワードは 422


class UserOut(Schema):
    id: int
    username: str  # password は返さない（書かない項目は応答に出ない）


class ProfileOut(Schema):
    user_id: int
    bio: str


class ProfileIn(Schema):
    bio: str


@router.post("/register", response={201: UserOut, 409: ErrorOut})
def register(request: HttpRequest, payload: RegisterIn):
    if User.objects.filter(username=payload.username).exists():
        return Status(409, {"detail": "そのユーザー名は使われています"})
    # create_user: パスワードをハッシュにしてから保存する
    user = User.objects.create_user(username=payload.username, password=payload.password)
    Profile.objects.create(user=user)  # 空のプロフィールを一緒に作る
    return Status(201, user)


@router.get("/me", response=ProfileOut, auth=JWTAuth())
def get_my_profile(request: HttpRequest):
    # user_id は一意なので、見つかるのは0件か1件
    return get_object_or_404(Profile, user_id=request.user.id)


@router.patch("/me", response=ProfileOut, auth=JWTAuth())
def update_my_profile(request: HttpRequest, payload: ProfileIn):
    profile = get_object_or_404(Profile, user_id=request.user.id)
    profile.bio = payload.bio
    profile.save()
    return profile
