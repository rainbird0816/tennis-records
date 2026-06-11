// 얇은 fetch 래퍼. /api 는 Vite 프록시 → FastAPI(:8000).

const BASE = "/api";

export async function api<T>(path: string, params?: Record<string, unknown>): Promise<T> {
  const qs = params
    ? "?" +
      new URLSearchParams(
        Object.entries(params)
          .filter(([, v]) => v !== undefined && v !== null)
          .map(([k, v]) => [k, String(v)]),
      ).toString()
    : "";
  const res = await fetch(`${BASE}${path}${qs}`);
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${path}`);
  }
  return res.json() as Promise<T>;
}
