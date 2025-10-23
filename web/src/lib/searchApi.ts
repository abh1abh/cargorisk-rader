// lib/searchApi.ts
import { SearchResponse } from "@/types";

export const PAGE_SIZE = 20;

export async function searchDocs({
  q,
  limit,
  offset,
  signal,
}: {
  q: string;
  limit: number;
  offset: number;
  signal?: AbortSignal;
}): Promise<SearchResponse> {
  const url = `/api/search?q=${encodeURIComponent(q)}&limit=${limit}&offset=${offset}`;
  const res = await fetch(url, { cache: "no-store", signal });
  if (!res.ok) {
    const msg = await res.text().catch(() => res.statusText);
    throw new Error(msg || `HTTP ${res.status}`);
  }
  return res.json();
}
