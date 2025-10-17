"use client";

import { useEffect, useRef, useState } from "react";
import { SearchHit } from "@/types";
import { useDebounced } from "@/hooks/useDebounced";
import { PAGE_SIZE, searchDocs } from "@/lib/searchApi";
import SearchBar from "./SearchBar";
import SearchResults from "./SearchResult";

export default function SearchClient() {
  const [query, setQuery] = useState("");
  const debouncedQ = useDebounced(query, 1000);

  const [items, setItems] = useState<SearchHit[]>([]);
  const [nextOffset, setNextOffset] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // cancel in-flight requests when a new one starts
  const abortRef = useRef<AbortController | null>(null);
  const reqIdRef = useRef(0);

  const [loadingMode, setLoadingMode] = useState<"idle" | "replace" | "append">("idle");

  useEffect(() => {
    if (!debouncedQ.trim()) {
      setItems([]);
      setNextOffset(null);
      setError(null);
      return;
    }
    runSearch({ q: debouncedQ, offset: 0, replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedQ]);

  async function runSearch({ q, offset, replace }: { q: string; offset: number; replace: boolean }) {
    const reqId = ++reqIdRef.current;
    abortRef.current?.abort();
    const ac = new AbortController();
    abortRef.current = ac;

    setLoading(true);
    setError(null);
    try {
      const data = await searchDocs({ q, limit: PAGE_SIZE, offset, signal: ac.signal });
      if (reqId !== reqIdRef.current) return; // stale response
      setItems((prev) => (replace ? data.results : [...(prev || []), ...data.results]));
      setNextOffset(data.next_offset);
    } catch (e: any) {
      if (e.name === "AbortError") return;
      setError(e.message || "Search error");
      if (replace) {
        setItems([]);
        setNextOffset(null);
      }
    } finally {
      if (reqId === reqIdRef.current) setLoading(false);
    }
  }

  const onSubmit = () => {
    if (query.trim()) runSearch({ q: query, offset: 0, replace: true });
  };

  const showEmpty = !loading && !error && debouncedQ && items.length === 0;

  return (
    <div className="p-6 space-y-4">
      <SearchBar
        value={query}
        onChange={setQuery}
        onSubmit={onSubmit}
        placeholder="Search documents… (e.g. Incoterms, BAF, free time)"
      />

      {error && <div className="text-sm text-red-600">Error: {error}</div>}
      {loading && items.length === 0 && <SkeletonList />}
      {showEmpty && <div className="text-sm text-gray-600">No results.</div>}

      <SearchResults
        items={items}
        query={debouncedQ}
        nextOffset={nextOffset}
        loading={loading}
        onLoadMore={() => nextOffset !== null && runSearch({ q: debouncedQ, offset: nextOffset, replace: false })}
      />

      <p>Immediate value: {query}</p>
      <p>Debounced value: {debouncedQ}</p>
    </div>
  );
}

function SkeletonList() {
  return (
    <ul className="space-y-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <li key={i} className="border rounded p-3 animate-pulse">
          <div className="h-4 w-40 bg-gray-200 rounded" />
          <div className="h-3 w-72 bg-gray-200 rounded mt-2" />
          <div className="h-16 w-full bg-gray-200 rounded mt-3" />
        </li>
      ))}
    </ul>
  );
}
