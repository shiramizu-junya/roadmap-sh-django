from ninja.testing import TestClient

from accounts.models import User
from blog.models import Post
from config.api import api

client = TestClient(api)


def test_mail_to_post_author(auth_headers: dict[str, str], mailoutbox) -> None:
    # bob の記事に、alice（auth_headers の持ち主）がコメントする
    bob = User.objects.create_user(username="bob", password="pass1234", email="bob@example.com")
    post = Post.objects.create(title="京都旅行", body="b", author=bob)
    client.post(f"/posts/{post.id}/comments", json={"body": "いいですね"}, headers=auth_headers)

    assert len(mailoutbox) == 1  # テスト中のメールは送られずに、ここに溜まる
    assert mailoutbox[0].to == ["bob@example.com"]
    assert "京都旅行" in mailoutbox[0].subject


def test_no_mail_for_own_post(user: User, auth_headers: dict[str, str], mailoutbox) -> None:
    user.email = "alice@example.com"
    user.save()
    post = Post.objects.create(title="t", body="b", author=user)
    client.post(f"/posts/{post.id}/comments", json={"body": "自分で"}, headers=auth_headers)
    assert len(mailoutbox) == 0


def test_no_mail_without_address(auth_headers: dict[str, str], mailoutbox) -> None:
    bob = User.objects.create_user(username="bob", password="pass1234")  # email なし
    post = Post.objects.create(title="t", body="b", author=bob)
    client.post(f"/posts/{post.id}/comments", json={"body": "x"}, headers=auth_headers)
    assert len(mailoutbox) == 0
