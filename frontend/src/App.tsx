import { useEffect, useState } from "react";

// 1件の商品（4-2 で、Ninja の OpenAPI から自動で作る型に置き換える）
type Product = {
    id: number;
    name: string;
    price: string;
    stock: number;
};

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
                    </li>
                ))}
            </ul>
        </main>
    );
}

export default App;
