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

        db.execute(text(f"SET LOCAL ivfflat.probes = {int(self.ivfflat_probes)}"))   

        sql = text("""
            SELECT id,
                    storage_uri,
                    LEFT(COALESCE(ocr_text,''), 200) AS snippet,
                    (embedding <-> :qvec)::float AS distance,
                    COUNT(*) OVER() AS total
            FROM media_assets
            WHERE embedding IS NOT NULL
            ORDER BY embedding <-> :qvec
            LIMIT :limit
            OFFSET :offset
        """)

        params = {"qvec": qvec, "limit": limit, "offset": offset}

        rows = db.execute(sql, params).mappings().all()
        if not rows:
            # one-time brute-force fallback
            db.execute(text("SET LOCAL enable_indexscan = off"))
            db.execute(text("SET LOCAL enable_bitmapscan = off"))
            rows = db.execute(sql, params).mappings().all()
        if rows:
            print(rows[0].keys())

        total = rows[0]["total"] if rows else 0

        results = [
            {
                "id": r["id"],
                "storage_uri": r["storage_uri"],
                "snippet": r["snippet"],
                "distance": r["distance"],
            } for r in rows
        ]
        ms = t()
        log.info("search_complete", extra={"duration": ms, "total": total, "returned": len(results)})

        return {"query": query, "results": results, "total": total}
