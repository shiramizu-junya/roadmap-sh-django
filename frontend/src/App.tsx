import type { components } from "./api/schema";
import { useEffect, useState } from "react";

// 1件の商品。Ninja の ProductOut から自動で作った型を使う
type Product = components["schemas"]["ProductOut"];

const API_URL = "http://127.0.0.1:8000/api";

function App() {
    const [products, setProducts] = useState<Product[]>([]);
    const [error, setError] = useState("");

    useEffect(() => {
        fetch(`${API_URL}/products`)
            .then((res) => res.json())
            .then((data: Product[]) => setProducts(data))
            .catch((e: unknown) => setError(String(e)));
    }, []);

    return (
        <main>
            <h1>商品一覧</h1>
            {error && <p>読み込めませんでした: {error}</p>}
            <ul>
                {products.map((p) => (
                    <li key={p.id}>
                        {p.name} — {p.price} 円（在庫 {p.stock}）
                        {p.rating_avg === null
                            ? " レビューなし"
                            : ` ★${p.rating_avg.toFixed(1)}（${p.review_count}件）`}
                    </li>
                ))}
            </ul>
        </main>
    );
}

export default App;
