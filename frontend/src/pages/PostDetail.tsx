import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";
import { getJson } from "../api/client";
import type { components } from "../api/schema";

type Post = components["schemas"]["PostOut"];

function PostDetail() {
    const { postId } = useParams(); // URL の /posts/:postId の部分（文字列）
    const [post, setPost] = useState<Post | null>(null);
    const [error, setError] = useState("");

    useEffect(() => {
        getJson<Post>(`/posts/${postId}`)
            .then((data) => setPost(data))
            .catch((e: unknown) => setError(String(e)));
    }, [postId]);

    if (error) return <p>読み込めませんでした: {error}</p>;
    if (post === null) return <p>読み込み中…</p>;

    return (
        <main>
            <p>
                <Link to="/">← 記事一覧へ</Link>
            </p>
            <h1>{post.title}</h1>
            <p>
                {post.category?.name ?? "カテゴリなし"} /{" "}
                {new Date(post.created_at).toLocaleString("ja-JP")}
            </p>
            <p>{post.tags.map((tag) => `#${tag.name}`).join(" ")}</p>
            <p>{post.body}</p>
        </main>
    );
}

export default PostDetail;
