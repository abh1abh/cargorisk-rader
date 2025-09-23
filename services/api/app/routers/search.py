from fastapi import APIRouter, Depends, Query
from pgvector.psycopg import Vector as PgVector
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..core.deps import get_db
from ..services.embeddings import embed_text

router = APIRouter(prefix="/search", tags=["search"])

@router.get("")
def search(q: str = Query(...), k: int = 5, db: Session = Depends(get_db)):
    emb = embed_text(q)
    qvec = PgVector(emb)
    sql = text("""
        SELECT id, storage_uri, left(ocr_text, 200) AS snippet,
               (embedding <-> :qvec)::float AS distance
        FROM media_assets
        WHERE embedding IS NOT NULL
        ORDER BY embedding <-> :qvec
        LIMIT :k
    """)
    rows = db.execute(sql, {"qvec": qvec, "k": k}).mappings().all()
    return {"query": q, "results": [dict(r) for r in rows]}
