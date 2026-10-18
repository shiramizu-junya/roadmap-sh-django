import pytest
from ninja.testing import TestClient

from accounts.models import Profile, User
from config.api import api

client = TestClient(api)


@pytest.mark.django_db
def test_register_creates_user_and_profile() -> None:
    res = client.post("/auth/register", json={"username": "carol", "password": "pass1234"})
    # TODO: 201 で、応答に password が無く、carol の Profile が1つできていること
    assert res.status_code == 201
    assert "password" not in res.json()
    assert Profile.objects.filter(user_id=res.json()["id"]).count() == 1


@pytest.mark.django_db
def test_registered_user_can_login() -> None:
    client.post("/auth/register", json={"username": "carol", "password": "pass1234"})
    res = client.post("/auth/login", json={"username": "carol", "password": "pass1234"})
    # TODO: 登録したパスワードでログインできること（200）
    assert res.status_code == 200


def test_duplicate_username_is_409(user: User) -> None:
    res = client.post("/auth/register", json={"username": user.username, "password": "pass1234"})
    # TODO: 409 で、ユーザーが増えていないこと
    assert res.status_code == 409
    assert User.objects.count() == 1


def test_update_my_profile(user: User, auth_headers: dict[str, str]) -> None:
    Profile.objects.create(user=user)
    res = client.patch("/auth/me", json={"bio": "よろしく"}, headers=auth_headers)
    # TODO: 200 で、DB の bio が書き換わっていること
    assert res.status_code == 200
    assert Profile.objects.get(user=user).bio == "よろしく"
