"use client";

import { SearchResponse } from "@/types";
import { useEffect, useMemo, useState } from "react";

const PAGE_SIZE = 20;

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1); // 1-based
  const debouncedQ = useDebounced(query, 1000);

  // for demo: set query to "Hello" when the page loads
  //   useEffect(() => {
  //     setQuery("Hello");
  //   }, []);

  // observe debouncedQ
  useEffect(() => {
    if (!debouncedQ?.trim()) {
      setResponse(null);
      setPage(1);
      return;
    }
    const ac = new AbortController();
    (async () => {
      setLoading(true);
      try {
        const offset = (page - 1) * PAGE_SIZE;
        const response = await fetch(
          `/api/search?q=${encodeURIComponent(debouncedQ)}&limit=${PAGE_SIZE}&offset=${offset}`,
          { cache: "no-store", signal: ac.signal }
        );
        if (!response.ok) throw new Error(await response.text());
        const data: SearchResponse = await response.json();
        setResponse(data);
      } catch (e) {
        if ((e as DOMException)?.name === "AbortError") {
          // Ignore abort errors
          return;
        }
        console.error(e);
        setResponse({ query: debouncedQ, results: [], total: 0 });
      } finally {
        setLoading(false);
      }
    })();
    return () => ac.abort();
  }, [debouncedQ, page]);

  const totalPages = useMemo(
    () => (response ? Math.max(1, Math.ceil(response.total / PAGE_SIZE)) : 1),
    [response]
  );

  function runNow() {
    // Force immediate search on button/Enter (reset to page 1)
    setPage(1);
    // touching q triggers effect via debouncedQ; we can also setResponse(null) to show loading skeleton
  }

  return (
    <div className="p-6 space-y-4">
      <div className="flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => (e.key === "Enter" ? runNow() : null)}
          placeholder="Search documents… (e.g. Incoterms, BAF, free time)"
          className="border p-2 rounded w-full"
        />
        <button onClick={runNow} className="px-3 py-2 border rounded">
          Search
        </button>
      </div>

      {loading && <div className="text-sm text-gray-600">Searching…</div>}

      {response?.results?.length === 0 && !loading && <div className="text-sm text-gray-600">No results.</div>}

      {response?.results?.length ? (
        <>
          <ul className="space-y-3">
            {response.results.map((r) => (
              <li key={r.id} className="border rounded p-3">
                <a className="font-medium underline" href={`/document/${r.id}`}>
                  Document #{r.id}
                </a>
                <div className="text-xs text-gray-600 mt-1 break-all">{r.storage_uri}</div>
                <pre className="text-sm mt-2 whitespace-pre-wrap">{r.snippet}…</pre>
              </li>
            ))}
          </ul>

          <div className="flex items-center gap-3 pt-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="px-2 py-1 border rounded disabled:opacity-50">
              Prev
            </button>
            <div className="text-sm">
              {page} / {totalPages}
            </div>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              className="px-2 py-1 border rounded disabled:opacity-50">
              Next
            </button>
          </div>
        </>
      ) : null}

      <p>Immediate value: {query}</p>
      <p>Debounced value: {debouncedQ}</p>
    </div>
  );
}

function useDebounced<T>(value: T, ms = 300) {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return v;
}
