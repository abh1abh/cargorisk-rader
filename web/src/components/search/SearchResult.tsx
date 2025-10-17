import { SearchHit } from "@/types";
import ResultItem from "./SearchItem";

export default function SearchResults({
  items,
  query,
  nextOffset,
  loading,
  onLoadMore,
}: {
  items: SearchHit[];
  query: string;
  nextOffset: number | null;
  loading: boolean;
  onLoadMore: () => void;
}) {
  if (!items.length) return null;

  return (
    <>
      <ul className="space-y-3">
        {items.map((r) => (
          <ResultItem key={r.id} r={r} query={query} />
        ))}
      </ul>
      <div className="pt-3">
        {nextOffset !== null ? (
          <button disabled={loading} onClick={onLoadMore} className="px-3 py-2 border rounded disabled:opacity-50">
            {loading ? "Loading…" : "Load more"}
          </button>
        ) : (
          <div className="text-xs text-gray-500 mt-2">End of results.</div>
        )}
      </div>
    </>
  );
}
