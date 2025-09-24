from fastapi import APIRouter, Depends, HTTPException, Query
from pgvector.psycopg import Vector as PgVector
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..core.deps import get_db
from ..services.embeddings import embed_text
from ..core.logging import get_logger, now_ms, request_id_ctx

log = get_logger("api.search")

router = APIRouter(prefix="/search", tags=["search"])

EMBED_DIM = 384  # keep in sync with your model


@router.get("")
def search(q: str = Query(...), k: int = 5, db: Session = Depends(get_db)):
    emb = embed_text(q)

    if EMBED_DIM and len(emb) != EMBED_DIM:
        raise HTTPException(status_code=500, detail="Embedding dimension mismatch")
    
    qvec = PgVector(emb)

    db.execute(text("SET LOCAL ivfflat.probes = 20"))

    sql = text("""
        SELECT id,
               storage_uri,
               LEFT(COALESCE(ocr_text,''), 200) AS snippet,
               (embedding <-> :qvec)::float AS distance
        FROM media_assets
        WHERE embedding IS NOT NULL
        ORDER BY embedding <-> :qvec
        LIMIT :k
    """)
    rows = db.execute(sql, {"qvec": qvec, "k": k}).mappings().all()
    if not rows:
        # one-time brute-force fallback
        db.execute(text("SET LOCAL enable_indexscan = off"))
        db.execute(text("SET LOCAL enable_bitmapscan = off"))
        rows = db.execute(sql, {"qvec": qvec, "k": k}).mappings().all()    
    return {"query": q, "results": [dict(r) for r in rows]}
