import SearchClient from "@/components/search/SearchClient";

export default function Page() {
  return <SearchClient />;
}

// "use client";

// import { SearchHit, SearchResponse } from "@/types";
// import { useEffect, useMemo, useRef, useState } from "react";

// const PAGE_SIZE = 20;

// export default function SearchPage() {
//   const [query, setQuery] = useState("");
//   const debouncedQ = useDebounced(query, 1000);

//   const [items, setItems] = useState<SearchHit[]>([]);
//   const [nextOffset, setNextOffset] = useState<number | null>(null);
//   const [loading, setLoading] = useState(false);
//   const [error, setError] = useState<string | null>(null);

//   // for demo: set query to "Hello" when the page loads
//   //   useEffect(() => {
//   //     setQuery("Hello");
//   //   }, []);

//   const reqIdRef = useRef(0);

//   // observe debouncedQ
//   useEffect(() => {
//     if (!debouncedQ?.trim()) {
//       setItems([]);
//       setNextOffset(null);
//       setError(null);
//       return;
//     }
//     runSearch({ q: debouncedQ, offset: 0, replace: true });
//   }, [debouncedQ]);

//   async function runSearch({ q, offset, replace }: { q: string; offset: number; replace: boolean }) {
//     const reqId = ++reqIdRef.current;
//     setLoading(true);
//     setError(null);
//     const ac = new AbortController();

//     try {
//       const url = `/api/search?q=${encodeURIComponent(q)}&limit=${PAGE_SIZE}&offset=${offset}`;
//       const res = await fetch(url, { cache: "no-store", signal: ac.signal });
//       if (!res.ok) {
//         const msg = await res.text().catch(() => res.statusText);
//         throw new Error(msg || `HTTP ${res.status}`);
//       }
//       const data: SearchResponse = await res.json();
//       if (reqId !== reqIdRef.current) return;

//       setItems((prev) => (replace ? data.results : [...(prev || []), ...data.results]));
//       setNextOffset(data.next_offset);
//     } catch (e: any) {
//       if (e.name === "AbortError") return;
//       setError(e.message || "Search error");
//       if (replace) {
//         setItems([]);
//         setNextOffset(null);
//       }
//     } finally {
//       if (reqId === reqIdRef.current) setLoading(false);
//     }
//     return () => ac.abort();
//   }

//   function onSubmit() {
//     if (query.trim()) runSearch({ q: query, offset: 0, replace: true });
//   }

//   const showEmpty = !loading && !error && debouncedQ && items.length === 0;

//   return (
//     <div className="p-6 space-y-4">
//       <div className="flex gap-2">
//         <input
//           value={query}
//           onChange={(e) => setQuery(e.target.value)}
//           onKeyDown={(e) => (e.key === "Enter" ? onSubmit() : null)}
//           placeholder="Search documents… (e.g. Incoterms, BAF, free time)"
//           className="border p-2 rounded w-full"
//         />
//         <button onClick={onSubmit} className="px-3 py-2 border rounded">
//           Search
//         </button>
//       </div>

//       {error && <div className="text-sm text-red-600">Error: {error}</div>}

//       {loading && <div className="text-sm text-gray-600">Searching…</div>}

//       {showEmpty && <div className="text-sm text-gray-600">No results.</div>}

//       {items.length > 0 && (
//         <>
//           <ul className="space-y-3">
//             {items.map((r) => (
//               <li key={r.id} className="border rounded p-3">
//                 <a className="font-medium underline" href={`/document/${r.id}`}>
//                   Document #{r.id}
//                 </a>
//                 <div className="text-xs text-gray-600 mt-1 break-all">{r.storage_uri}</div>
//                 <pre className="text-sm mt-2 whitespace-pre-wrap">{highlight(r.snippet, debouncedQ)}……</pre>
//                 {(r.score !== undefined || r.distance !== undefined || r.bm25 !== undefined) && (
//                   <div className="flex gap-2 mt-2 text-[11px] text-gray-500">
//                     {r.score !== undefined && <span>score: {round(r.score, 4)}</span>}
//                     {r.distance !== undefined && <span>dist: {round(r.distance, 4)}</span>}
//                     {r.bm25 !== undefined && <span>bm25: {round(r.bm25, 4)}</span>}
//                   </div>
//                 )}
//               </li>
//             ))}
//           </ul>

//           <div className="pt-3">
//             {nextOffset !== null ? (
//               <button
//                 disabled={loading}
//                 onClick={() => runSearch({ q: debouncedQ, offset: nextOffset!, replace: false })}
//                 className="px-3 py-2 border rounded disabled:opacity-50">
//                 {loading ? "Loading…" : "Load more"}
//               </button>
//             ) : (
//               <div className="text-xs text-gray-500 mt-2">End of results.</div>
//             )}
//           </div>
//         </>
//       )}

//       <p>Immediate value: {query}</p>
//       <p>Debounced value: {debouncedQ}</p>
//     </div>
//   );
// }

// function useDebounced<T>(value: T, ms = 300) {
//   const [v, setV] = useState(value);
//   useEffect(() => {
//     const t = setTimeout(() => setV(value), ms);
//     return () => clearTimeout(t);
//   }, [value, ms]);
//   return v;
// }

// /** highlight query terms in the snippet (basic, case-insensitive) */
// function highlight(text: string, q: string) {
//   if (!q) return text;
//   try {
//     const escaped = q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
//     const re = new RegExp(`(${escaped})`, "ig");
//     const parts = text.split(re);
//     return parts.map((p, i) =>
//       re.test(p) ? (
//         <mark key={i} className="bg-yellow-200">
//           {p}
//         </mark>
//       ) : (
//         <span key={i}>{p}</span>
//       )
//     );
//   } catch {
//     return text;
//   }
// }

// function round(n: number, digits = 3) {
//   const f = Math.pow(10, digits);
//   return Math.round(n * f) / f;
// }
