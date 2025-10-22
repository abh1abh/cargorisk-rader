import "server-only";

const INTERNAL_API_URL =
  process.env.INTERNAL_API_URL ?? (process.env.DOCKER ? "http://api:8000" : "http://localhost:8000");
// console.log("INTERNAL_API_URL", INTERNAL_API_URL);

// Simple wrapper around fetch() to call our internal API
// Usage: api<Type>(path, init?)
// Note: this runs server-side only, so we can use the internal Docker network address
// and avoid CORS issues. Client-side code should call /api/* directly.
export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  console.log("INTERNAL_API_URL", INTERNAL_API_URL);

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

// Get the Location header from a redirecting endpoint (e.g. 302/303/307/308)
export async function apiRedirectLocation(path: string, init?: RequestInit): Promise<string> {
  const url = `${INTERNAL_API_URL}${path}`;
  const r = await fetch(url, {
    ...init,
    cache: "no-store",
    redirect: "manual", // <- DO NOT follow the redirect
  });

  // Expect a redirect status
  if (r.status >= 300 && r.status < 400) {
    const loc = r.headers.get("location");
    if (!loc) throw new Error(`Missing Location header on ${path}`);
    return loc; // should be the presigned S3 URL
  }

  // If your backend ever streams the file directly instead of redirecting
  throw new Error(`Expected redirect, got HTTP ${r.status} on ${path}`);
}
