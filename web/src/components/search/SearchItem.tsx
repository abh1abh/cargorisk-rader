import { SearchHit } from "@/types";

export default function ResultItem({ r, query }: { r: SearchHit; query: string }) {
  return (
    <li className="border rounded p-3">
      <a className="font-medium underline" href={`/document/${r.id}`}>
        Document #{r.id}
      </a>
      <div className="text-xs text-gray-600 mt-1 break-all">{r.storage_uri}</div>
      <pre className="text-sm mt-2 whitespace-pre-wrap">{highlight(r.snippet, query)}……</pre>
      {(r.score !== undefined || r.distance !== undefined || r.bm25 !== undefined) && (
        <div className="flex gap-2 mt-2 text-[11px] text-gray-500">
          {r.score !== undefined && <span>score: {round(r.score, 4)}</span>}
          {r.distance !== undefined && <span>dist: {round(r.distance, 4)}</span>}
          {r.bm25 !== undefined && <span>bm25: {round(r.bm25, 4)}</span>}
        </div>
      )}
    </li>
  );
}

function highlight(text: string, q: string) {
  if (!q) return text;
  try {
    const escaped = q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const re = new RegExp(`(${escaped})`, "ig");
    const parts = text.split(re);
    return parts.map((p, i) =>
      i % 2 === 1 ? (
        <mark key={i} className="bg-yellow-200">
          {p}
        </mark>
      ) : (
        <span key={i}>{p}</span>
      )
    );
  } catch {
    return text;
  }
}
export function round(n: number, digits = 3) {
  const f = Math.pow(10, digits);
  return Math.round(n * f) / f;
}
