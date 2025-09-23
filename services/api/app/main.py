import boto3
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from .core.config import settings
from .core.deps import get_db
from .core.http_logging import http_logging_middleware
from .core.logging import setup_logging
from .routers import documents, jobs, search, upload

setup_logging()  # before creating app/logging
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(http_logging_middleware)


@app.get("/health")
def health():
    return {"status": "ok", "bucket": settings.s3_bucket}

@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT id, type, storage_uri, sha256, created_at FROM media_assets LIMIT 20"))
    # Convert SQLAlchemy Row -> dict
    results = [dict(r._mapping) for r in rows]
    return {
        "db": "ok",
        "media_assets": results,
        "count": len(results),
    }

@app.get("/health/s3")
def health_s3():
    s3 = boto3.client("s3",
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key
    )
    buckets = [b["Name"] for b in s3.list_buckets()["Buckets"]]
    return {"s3": "ok", "buckets": buckets}


app.include_router(upload.router)
app.include_router(jobs.router)

app.include_router(documents.router)

app.include_router(search.router)



