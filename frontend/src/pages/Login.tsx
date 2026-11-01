import { useState } from "react";
import type { SubmitEvent } from "react";
import { useNavigate } from "react-router";
import { login } from "../api/client";

function Login() {
    const navigate = useNavigate();
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");

    function handleSubmit(e: SubmitEvent<HTMLFormElement>) {
        e.preventDefault(); // フォームの既定の送信（ページの読み込み直し）を止める
        login(username, password)
            .then(() => navigate("/orders")) // ログインできたら注文履歴へ
            .catch((e: unknown) => setError(String(e)));
    }

    return (
        <main>
            <h1>ログイン</h1>
            {error && <p>ログインできませんでした: {error}</p>}
            <form onSubmit={handleSubmit}>
                <p>
                    <label>
                        ユーザー名{" "}
                        <input
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                        />
                    </label>
                </p>
                <p>
                    <label>
                        パスワード{" "}
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                    </label>
                </p>
                <button type="submit">ログイン</button>
            </form>
        </main>
    );
}

export default Login;
