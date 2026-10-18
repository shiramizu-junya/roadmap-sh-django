from ninja.testing import TestClient

from accounts.models import User
from blog.models import Comment, Post
from config.api import api

client = TestClient(api)


def test_reply_is_nested(user: User, auth_headers: dict[str, str]) -> None:
    post = Post.objects.create(title="t", body="b", author=user)
    url = f"/posts/{post.id}/comments"
    first = client.post(url, json={"body": "最初"}, headers=auth_headers).json()
    client.post(url, json={"body": "返信", "parent_id": first["id"]}, headers=auth_headers)

    res = client.get(url)
    assert res.status_code == 200
    assert len(res.json()) == 1  # 一覧の一番上には、最初のコメントだけ
    assert res.json()[0]["replies"][0]["body"] == "返信"


def test_reply_to_other_posts_comment_is_404(user: User, auth_headers: dict[str, str]) -> None:
    post_a = Post.objects.create(title="a", body="b", author=user)
    post_b = Post.objects.create(title="b", body="b", author=user)
    other = Comment.objects.create(post=post_b, author=user, body="b の記事のコメント")

    res = client.post(
        f"/posts/{post_a.id}/comments",
        json={"body": "x", "parent_id": other.id},
        headers=auth_headers,
    )
    assert res.status_code == 404
    assert Comment.objects.count() == 1


def test_reply_to_reply_is_400(user: User, auth_headers: dict[str, str]) -> None:
    post = Post.objects.create(title="t", body="b", author=user)
    first = Comment.objects.create(post=post, author=user, body="最初")
    reply = Comment.objects.create(post=post, author=user, parent=first, body="返信")

    res = client.post(
        f"/posts/{post.id}/comments",
        json={"body": "返信の返信", "parent_id": reply.id},
        headers=auth_headers,
    )
    assert res.status_code == 400


def test_deleting_parent_deletes_replies(user: User) -> None:
    post = Post.objects.create(title="t", body="b", author=user)
    first = Comment.objects.create(post=post, author=user, body="最初")
    Comment.objects.create(post=post, author=user, parent=first, body="返信")

    first.delete()
    assert Comment.objects.count() == 0
