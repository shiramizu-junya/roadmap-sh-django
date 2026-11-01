import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router";
import { getJsonWithAuth, logout } from "../api/client";
import type { components } from "../api/schema";

type Order = components["schemas"]["OrderOut"];

// 注文の状態の、画面に出す名前。Status の3つのどれかが抜けると、型のエラーになる
const STATUS_LABEL: Record<components["schemas"]["Status"], string> = {
    placed: "確定",
    shipped: "発送済み",
    completed: "完了",
};

function OrderList() {
    const navigate = useNavigate();
    const [orders, setOrders] = useState<Order[] | null>(null);
    const [error, setError] = useState("");

    useEffect(() => {
        getJsonWithAuth<Order[]>("/orders")
            .then((data) => setOrders(data))
            .catch((e: unknown) => setError(String(e)));
    }, []);

    function handleLogout() {
        logout();
        navigate("/login");
    }

    if (error) {
        return (
            <main>
                <p>読み込めませんでした: {error}</p>
                <p>
                    <Link to="/login">ログインする</Link>
                </p>
            </main>
        );
    }
    if (orders === null) return <p>読み込み中…</p>;

    return (
        <main>
            <h1>注文履歴</h1>
            <button onClick={handleLogout}>ログアウト</button>
            <ul>
                {orders.map((order) => (
                    <li key={order.id}>
                        注文 {order.id}（{STATUS_LABEL[order.status]}）— 合計{" "}
                        {order.total} 円
                        <ul>
                            {order.items.map((item) => (
                                <li key={item.product_id}>
                                    {item.name} × {item.quantity}
                                </li>
                            ))}
                        </ul>
                    </li>
                ))}
            </ul>
        </main>
    );
}

export default OrderList;
