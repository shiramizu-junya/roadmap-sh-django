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
