import { useEffect, useState } from "react";
import { Link } from "react-router";
import { getJson } from "../api/client";
import type { components } from "../api/schema";

// 記事の一覧。@paginate なので {"items": [...], "count": 全件数} の形（2-12）
type PagedPosts = components["schemas"]["PagedPostOut"];

function PostList() {
    const [page, setPage] = useState<PagedPosts | null>(null);
    const [error, setError] = useState("");

    useEffect(() => {
        getJson<PagedPosts>("/posts")
            .then((data) => setPage(data))
            .catch((e: unknown) => setError(String(e)));
    }, []);

    if (error) return <p>読み込めませんでした: {error}</p>;
    if (page === null) return <p>読み込み中…</p>;

    return (
        <main>
            <h1>記事一覧（{page.count}件）</h1>
            <ul>
                {page.items.map((post) => (
                    <li key={post.id}>
                        <Link to={`/posts/${post.id}`}>{post.title}</Link>
                        {post.category && `（${post.category.name}）`}
                    </li>
                ))}
            </ul>
        </main>
    );
}

export default PostList;
