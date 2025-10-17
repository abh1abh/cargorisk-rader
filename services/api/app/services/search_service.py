import code
from dataclasses import dataclass

from pgvector.psycopg import Vector as PgVector
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..core.logging import get_logger
from ..core.metrics import timed
from ..services.embedding_service import EmbeddingService

log = get_logger("svc.search")

class BadRequest(ValueError):
    pass


class ProcessingError(RuntimeError):
    pass


@dataclass(slots=True)
class SearchService:
    embedder: EmbeddingService
    embed_dim: int | None = 384 # keep in sync with your model
    ivfflat_probes: int = 20  # number of probes for ivfflat index scan

    def search(self, db: Session, query: str, limit: int = 5, offset: int = 0) -> dict:
        if not query or not query.strip():
            return {"query": query, "results": [], "total": 0} # raise BadRequest("Empty query")
    
        t = timed("search")
        log.info("search_start", extra={"limit": limit, "offset": offset})
        try:
            emb = self.embedder.embed_text(query)
        except Exception as e:
            ms = t()
            log.error("search_embedding_failed", extra={"error": e.__class__.__name__, "duration": ms})
            raise ProcessingError("Failed to embed query") from e
        if self.embed_dim and len(emb) != self.embed_dim:
            ms = t()
            log.warning("search_embedding_dim_mismatch", extra={"duration": ms, "expected": self.embed_dim, "actual": len(emb)})
            raise ProcessingError("Embedding dimension mismatch")
        
        qvec = PgVector(emb)


        candidates = max(limit * 10, 100)  # widen then re-rank
        probes = max(1, min(int(self.ivfflat_probes), 1024))

        sql = text("""
            WITH ann AS (
                SELECT id, storage_uri, ocr_text,
                       (embedding <-> :qvec)::float AS distance
                FROM media_assets
                WHERE embedding IS NOT NULL
                ORDER BY (embedding <-> :qvec), id ASC
                LIMIT :candidates
            ),
            lex AS (
                SELECT id,
                       ts_rank_cd(
                         to_tsvector('simple', coalesce(ocr_text,'')),
                         plainto_tsquery('simple', :qtext)
                       ) AS bm25
                FROM media_assets
                WHERE to_tsvector('simple', coalesce(ocr_text,'')) @@ plainto_tsquery('simple', :qtext)
            )
            SELECT a.id,
                   a.storage_uri,
                   LEFT(coalesce(a.ocr_text,''), 200) AS snippet,
                   a.distance,
                   coalesce(l.bm25, 0) AS bm25,
                   (0.7 * (1 - LEAST(1.0, a.distance)) + 0.3 * coalesce(l.bm25,0)) AS score
            FROM ann a
            LEFT JOIN lex l USING (id)
            ORDER BY score DESC, a.distance ASC, a.id ASC
            LIMIT :limit OFFSET :offset
        """)

        params = {
            "qvec": qvec,
            "qtext": query,
            "candidates": candidates,
            "limit": limit,
            "offset": offset,
        }
        try:
            with db.begin():
                # set ivfflat.probes for this transaction
                db.execute(text(f"SET LOCAL statement_timeout = '5s'"))
                db.execute(text(f"SET LOCAL ivfflat.probes = {probes}"))

                rows = db.execute(sql, params).mappings().all()
                fallback_used = False
                if not rows:
                    # one-time brute-force fallback
                    db.execute(text("SET LOCAL enable_indexscan = off"))
                    db.execute(text("SET LOCAL enable_bitmapscan = off"))
                    rows = db.execute(sql, params).mappings().all()
                    fallback_used = True
                if rows:
                    print(rows[0].keys())
        except Exception as e:
            ms = t()
            log.error(
                "search_db_failed",
                extra={
                    "duration": ms,
                    "sqlstate": getattr(e, "orig", {}).get("pgcode", "N/A"),
                    "exc": e.__class__.__name__,
                    "probes": probes,
                    "candidates": candidates,
                },
            )
            raise ProcessingError("Search failed due to a database error.") from e

        results = [
            {
                "id": r["id"],
                "storage_uri": r["storage_uri"],
                "snippet": r["snippet"],
                "distance": r["distance"],
                "score": r["score"],
                "bm25": r["bm25"],
            }
            for r in rows
        ]
        next_offset = (offset + limit) if len(results) == limit else None

        ms = t()

        log.info(
            "search_complete",
            extra={
                "duration": ms,
                "returned": len(results),
                "probes": probes,
                "candidates": candidates,
                "fallback": fallback_used,
                "next_offset": next_offset,
            },
        )

        return {"query": query, "results": results, "next_offset": next_offset}
