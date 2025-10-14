import "server-only";

const INTERNAL_API_URL =
  process.env.INTERNAL_API_URL ?? (process.env.DOCKER ? "http://api:8000" : "http://localhost:8000");
console.log("INTERNAL_API_URL", INTERNAL_API_URL);

// Simple wrapper around fetch() to call our internal API
// Usage: api<Type>(path, init?)
// Note: this runs server-side only, so we can use the internal Docker network address
// and avoid CORS issues. Client-side code should call /api/* directly.
export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${INTERNAL_API_URL}${path}`;
  console.log("fetch", url);
  const r = await fetch(url, { ...init, cache: "no-store" });
  if (!r.ok) {
    // surface backend error text
    const msg = await r.text().catch(() => "");
    throw new Error(msg || `HTTP ${r.status} on ${path}`);
  }
  return r.json() as Promise<T>;
}
