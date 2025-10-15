from fastapi import APIRouter, Depends, HTTPException, Query
from pgvector.psycopg import Vector as PgVector
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..core.deps import EmbeddingDependency, get_db
from ..core.logging import get_logger

log = get_logger("api.search")

router = APIRouter(prefix="/search", tags=["search"])

EMBED_DIM = 384  # keep in sync with your model


@router.get("")
def search(embedder: EmbeddingDependency, q: str = Query(...), limit: int = 5, offset: int = 0, db: Session = Depends(get_db)):
    emb = embedder.embed_text(q)

    if EMBED_DIM and len(emb) != EMBED_DIM:
        raise HTTPException(status_code=500, detail="Embedding dimension mismatch")
    
    qvec = PgVector(emb)

    db.execute(text("SET LOCAL ivfflat.probes = 20"))

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
    rows = db.execute(sql, {"qvec": qvec, "limit": limit, "offset": offset}).mappings().all()
    if not rows:
        # one-time brute-force fallback
        db.execute(text("SET LOCAL enable_indexscan = off"))
        db.execute(text("SET LOCAL enable_bitmapscan = off"))
        rows = db.execute(sql, {"qvec": qvec, "limit": limit, "offset": offset}).mappings().all()
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

    return {"query": q, "results": results, "total": total}
