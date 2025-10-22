from contextlib import asynccontextmanager
# import asyncio
# from anyio import to_thread
import boto3
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from .core.config import Settings, get_settings
from .core.deps import get_db #, _s3_singleton, get_embedding_model, get_ocr_service
from .core.http_logging import http_logging_middleware
from .core.logging import setup_logging
from .routers import document, job, search, upload

setup_logging()  # before creating app/logging

# _WARMED_UP = asyncio.Event()

# async def _warm_heavy_singletons():
#     try:
#         await asyncio.gather(
#             to_thread.run_sync(get_embedding_model),  # blocking
#             to_thread.run_sync(_s3_singleton),        # blocking
#             to_thread.run_sync(get_ocr_service),      # blocking
#         )
#     finally:
#         _WARMED_UP.set()  # set even if partial failures; or set only on success

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     asyncio.create_task(_warm_heavy_singletons())  # don’t block startup
#     yield


# app = FastAPI(lifespan=lifespan)
app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(http_logging_middleware)


# TODO: Move to route 
@app.get("/live")
def live():
    return {"status": "up"}

# @app.get("/ready")
# async def ready():
#     return {"status": "ok" if _WARMED_UP.is_set() else "warming"}

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
def health_s3(settings: Settings = Depends(get_settings)):
    s3 = boto3.client("s3",
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key
    )
    buckets = [b["Name"] for b in s3.list_buckets()["Buckets"]]
    return {"s3": "ok", "buckets": buckets}


app.include_router(upload.router)

app.include_router(job.router)

app.include_router(document.router)

app.include_router(search.router)



