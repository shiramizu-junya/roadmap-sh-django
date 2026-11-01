import type { components } from "./schema";

type TokenOut = components["schemas"]["TokenOut"];
type AccessOut = components["schemas"]["AccessOut"];

// API の住所。画面ごとに書かず、ここ1か所にまとめる
export const API_URL = "http://127.0.0.1:8000/api";

// GET して、返ってきた JSON を T 型として返す
export async function getJson<T>(path: string): Promise<T> {
    const res = await fetch(`${API_URL}${path}`);
    if (!res.ok) {
        // fetch は 404 や 500 では例外にしない。2xx 以外は、ここで例外にする
        throw new Error(`${res.status} ${res.statusText}`);
    }
    return (await res.json()) as T;
}

// ログインして、身分証（access）と引換券（refresh）をブラウザに保存する
export async function login(username: string, password: string): Promise<void> {
    const res = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
        throw new Error(`${res.status} ${res.statusText}`);
    }
    const tokens = (await res.json()) as TokenOut;
    localStorage.setItem("access", tokens.access);
    localStorage.setItem("refresh", tokens.refresh);
}

// ログアウト。保存した身分証と引換券を消す
export function logout(): void {
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
}

// 身分証を Authorization ヘッダに付けて GET する
function fetchWithAccess(path: string): Promise<Response> {
    return fetch(`${API_URL}${path}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("access")}` },
    });
}

// 引換券で、新しい身分証をもらう。引換券が無いか切れていたら、ログアウトして false
async function refreshAccess(): Promise<boolean> {
    const refresh = localStorage.getItem("refresh");
    if (refresh === null) {
        return false;
    }
    const res = await fetch(`${API_URL}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh }),
    });
    if (!res.ok) {
        logout();
        return false;
    }
    const data = (await res.json()) as AccessOut;
    localStorage.setItem("access", data.access);
    return true;
}

// ログインが要る API を GET して、返ってきた JSON を T 型として返す
export async function getJsonWithAuth<T>(path: string): Promise<T> {
    let res = await fetchWithAccess(path);
    if (res.status === 401 && (await refreshAccess())) {
        // 身分証が切れていた。新しい身分証で、1回だけやり直す
        res = await fetchWithAccess(path);
    }
    if (!res.ok) {
        throw new Error(`${res.status} ${res.statusText}`);
    }
    return (await res.json()) as T;
}
