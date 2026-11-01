import { useEffect, useState } from "react";
import { getJson, postJsonWithAuth } from "../api/client";
import type { components } from "../api/schema";

// 1件の商品。Ninja の ProductOut から自動で作った型を使う
type Product = components["schemas"]["ProductOut"];
type CartItemOut = components["schemas"]["CartItemOut"];

function ProductList() {
    const [products, setProducts] = useState<Product[]>([]);
    const [error, setError] = useState("");
    const [message, setMessage] = useState(""); // カートに入れた結果

    useEffect(() => {
        getJson<Product[]>("/products")
            .then((data) => setProducts(data))
            .catch((e: unknown) => setError(String(e)));
    }, []);

    function handleAdd(product: Product) {
        postJsonWithAuth<CartItemOut>("/cart/items", {
            product_id: product.id,
            quantity: 1,
        })
            .then((item) =>
                setMessage(
                    `「${item.name}」をカートに入れました（${item.quantity}個）`,
                ),
            )
            .catch((e: unknown) =>
                setMessage(`カートに入れられませんでした: ${String(e)}`),
            );
    }

    return (
        <main>
            <h1>商品一覧</h1>
            {error && <p>読み込めませんでした: {error}</p>}
            {message && <p>{message}</p>}
            <ul>
                {products.map((p) => (
                    <li key={p.id}>
                        {p.name} — {p.price} 円（在庫 {p.stock}）
                        {p.rating_avg === null
                            ? " レビューなし"
                            : ` ★${p.rating_avg.toFixed(1)}（${p.review_count}件）`}{" "}
                        <button
                            disabled={p.stock === 0}
                            onClick={() => handleAdd(p)}
                        >
                            {p.stock === 0 ? "売り切れ" : "カートに入れる"}
                        </button>
                    </li>
                ))}
            </ul>
        </main>
    );
}

export default ProductList;
