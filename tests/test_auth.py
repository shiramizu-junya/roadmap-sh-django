import pytest
from ninja.testing import TestClient

from accounts.models import User
from config.api import api

client = TestClient(api)


@pytest.mark.django_db
def test_login_returns_tokens() -> None:
    User.objects.create_user(username="alice", password="pass1234")
    res = client.post("/auth/login", json={"username": "alice", "password": "pass1234"})
    # TODO: 200 で、access と refresh の両方が返ること
    assert res.status_code == 200
    assert set(res.json()) == {"access", "refresh"}


@pytest.mark.django_db
def test_wrong_password_is_401() -> None:
    User.objects.create_user(username="alice", password="pass1234")
    res = client.post("/auth/login", json={"username": "alice", "password": "wrong"})
    # TODO: 401 で、トークンを返さないこと
    assert res.status_code == 401
    assert "access" not in res.json()


@pytest.mark.django_db
def test_refresh_gives_new_access() -> None:
    User.objects.create_user(username="alice", password="pass1234")
    tokens = client.post("/auth/login", json={"username": "alice", "password": "pass1234"}).json()
    # TODO: refresh を渡すと 200。access を渡すと 401（種類が違う）
    assert client.post("/auth/refresh", json={"refresh": tokens["refresh"]}).status_code == 200
    assert client.post("/auth/refresh", json={"refresh": tokens["access"]}).status_code == 401
