import io
from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from ninja.testing import TestClient
from PIL import Image

from accounts.models import User
from blog.models import Post, PostImage
from config.api import api

client = TestClient(api)


@pytest.fixture(autouse=True)
def media_in_tmp(settings, tmp_path: Path) -> None:
    # テストで保存するファイルは、使い捨てのフォルダに置く（本物の media/ を汚さない）
    settings.MEDIA_ROOT = tmp_path


def png_file(name: str = "red.png") -> SimpleUploadedFile:
    # Pillow で 1x1 の PNG を作り、アップロードされたファイルの形にする
    buf = io.BytesIO()
    Image.new("RGB", (1, 1), "red").save(buf, "PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


def test_upload_saves_file(user: User, auth_headers: dict[str, str], tmp_path: Path) -> None:
    post = Post.objects.create(title="t", body="b", author=user)
    res = client.post(f"/posts/{post.id}/images", FILES={"file": png_file()}, headers=auth_headers)
    assert res.status_code == 201
    assert res.json()["url"] == "/media/posts/red.png"
    assert (tmp_path / "posts" / "red.png").exists()  # ファイルが MEDIA_ROOT に置かれた


def test_not_image_is_400(user: User, auth_headers: dict[str, str]) -> None:
    post = Post.objects.create(title="t", body="b", author=user)
    fake = SimpleUploadedFile("fake.png", b"hello", content_type="image/png")
    res = client.post(f"/posts/{post.id}/images", FILES={"file": fake}, headers=auth_headers)
    assert res.status_code == 400
    assert PostImage.objects.count() == 0


def test_other_users_post_is_403(auth_headers: dict[str, str]) -> None:
    bob = User.objects.create_user(username="bob", password="pass1234")
    post = Post.objects.create(title="t", body="b", author=bob)
    res = client.post(f"/posts/{post.id}/images", FILES={"file": png_file()}, headers=auth_headers)
    assert res.status_code == 403
