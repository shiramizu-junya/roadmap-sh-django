import pytest
from ninja_jwt.tokens import RefreshToken

from accounts.models import User


@pytest.fixture
def user(db) -> User:
    # ログインしている人。引数に user と書いたテストに渡される
    return User.objects.create_user(username="alice", password="pass1234")


@pytest.fixture
def auth_headers(user: User) -> dict[str, str]:
    # user の身分証を、リクエストのヘッダの形にする
    token = RefreshToken.for_user(user).access_token  # type: ignore[misc]
    return {"Authorization": f"Bearer {token}"}
