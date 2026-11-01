import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { getJsonWithAuth, postJsonWithAuth } from "../api/client";
import type { components } from "../api/schema";

type CartOut = components["schemas"]["CartOut"];
type OrderOut = components["schemas"]["OrderOut"];

function Cart() {
    const navigate = useNavigate();
    const [cart, setCart] = useState<CartOut | null>(null);
    const [loadError, setLoadError] = useState("");
    const [orderError, setOrderError] = useState("");
    const [sending, setSending] = useState(false); // 注文を送っている間は true

    useEffect(() => {
        getJsonWithAuth<CartOut>("/cart")
            .then((data) => setCart(data))
            .catch((e: unknown) => setLoadError(String(e)));
    }, []);

    function handleOrder() {
        setSending(true);
        postJsonWithAuth<OrderOut>("/orders")
            .then(() => navigate("/orders")) // 確定したら注文履歴へ
            .catch((e: unknown) => {
                setOrderError(String(e));
                setSending(false);
            });
    }

    if (loadError) return <p>読み込めませんでした: {loadError}</p>;
    if (cart === null) return <p>読み込み中…</p>;

    return (
        <main>
            <h1>カート</h1>
            {orderError && <p>注文できませんでした: {orderError}</p>}
            {cart.items.length === 0 ? (
                <p>カートは空です</p>
            ) : (
                <>
                    <ul>
                        {cart.items.map((item) => (
                            <li key={item.product_id}>
                                {item.name} — {item.price} 円 × {item.quantity}
                            </li>
                        ))}
                    </ul>
                    <p>合計 {cart.total} 円</p>
                    <button disabled={sending} onClick={handleOrder}>
                        {sending ? "注文しています…" : "注文を確定する"}
                    </button>
                </>
            )}
        </main>
    );
}

export default Cart;
