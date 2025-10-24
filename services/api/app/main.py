import asyncio
from contextlib import asynccontextmanager

from anyio import to_thread
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from .core.config import Settings, get_settings
from .core.deps import _s3_singleton, get_db, get_embedding_model, get_ocr_service
from .core.http_logging import http_logging_middleware
from .core.logging import get_logger, setup_logging
from .infra.llm_extractor_hf import HfQwenFreightExtractor
from .routers import document, job, search, upload

log = get_logger("entry")
log.info("Starting api...")

setup_logging()  # before creating app/logging

_WARMED_UP = asyncio.Event()

async def _warm_heavy_singletons():
    try:
        await asyncio.gather(
            to_thread.run_sync(get_embedding_model),  # blocking
            to_thread.run_sync(_s3_singleton),        # blocking
            to_thread.run_sync(get_ocr_service),      # blocking
        )
    finally:
        _WARMED_UP.set()  # set even if partial failures; or set only on success

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.warmup_task = asyncio.create_task(_warm_heavy_singletons())
    yield
    await app.state.warmup_task




app = FastAPI(lifespan=lifespan)
# app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(http_logging_middleware)


# TODO: Move to route 
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/ready")
async def ready():
    return {"status": "ok" if _WARMED_UP.is_set() else "warming"}

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

@app.get("/testmodel/{asset_id}")
def test_model( asset_id: int, settings: Settings = Depends(get_settings), db: Session = Depends(get_db),):
    
    # asset = db.get(MediaAsset, asset_id)
    model = HfQwenFreightExtractor(api_key=settings.hf_api_key, base_url=settings.hf_base_url)
    r = model.test()
    return r


app.include_router(upload.router)

app.include_router(job.router)

app.include_router(document.router)

app.include_router(search.router)



