import type { components } from "./schema";

type TokenOut = components["schemas"]["TokenOut"];
type AccessOut = components["schemas"]["AccessOut"];

// API の住所。画面ごとに書かず、ここ1か所にまとめる
export const API_URL = "http://127.0.0.1:8000/api";

// 失敗した応答から、例外を作る。Django の HttpError は {"detail": "理由"} を返すので、読めたら理由を使う
async function errorFrom(res: Response): Promise<Error> {
    const body = (await res.json().catch(() => null)) as {
        detail?: unknown;
    } | null;
    const detail =
        typeof body?.detail === "string" ? body.detail : res.statusText;
    return new Error(`${res.status} ${detail}`);
}

// GET して、返ってきた JSON を T 型として返す
export async function getJson<T>(path: string): Promise<T> {
    const res = await fetch(`${API_URL}${path}`);
    if (!res.ok) {
        // fetch は 404 や 500 では例外にしない。2xx 以外は、ここで例外にする
        throw await errorFrom(res);
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
        throw await errorFrom(res);
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

// 身分証を Authorization ヘッダに付けて呼ぶ。body を渡したら、JSON にして送る
function fetchWithAccess(
    path: string,
    method: string,
    body?: unknown,
): Promise<Response> {
    const headers: Record<string, string> = {
        Authorization: `Bearer ${localStorage.getItem("access")}`,
    };
    if (body !== undefined) {
        headers["Content-Type"] = "application/json";
    }
    return fetch(`${API_URL}${path}`, {
        method,
        headers,
        body: body === undefined ? undefined : JSON.stringify(body),
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

// ログインが要る API を呼んで、返ってきた JSON を T 型として返す
async function sendWithAuth<T>(
    path: string,
    method: string,
    body?: unknown,
): Promise<T> {
    let res = await fetchWithAccess(path, method, body);
    if (res.status === 401 && (await refreshAccess())) {
        // 身分証が切れていた。新しい身分証で、1回だけやり直す
        res = await fetchWithAccess(path, method, body);
    }
    if (!res.ok) {
        throw await errorFrom(res);
    }
    return (await res.json()) as T;
}

// ログインが要る API を GET する
export function getJsonWithAuth<T>(path: string): Promise<T> {
    return sendWithAuth<T>(path, "GET");
}

// ログインが要る API に POST する。body は JSON にして送る
export function postJsonWithAuth<T>(path: string, body?: unknown): Promise<T> {
    return sendWithAuth<T>(path, "POST", body);
}
