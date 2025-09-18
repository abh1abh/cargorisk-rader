from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..core.deps import get_db
from ..models import MediaAsset
from ..core.s3 import get_s3, S3Service
from ..core.config import settings
from celery import Celery
import os

router = APIRouter(prefix="/upload", tags=["upload"])

# Celery client (broker/backend default to local Redis if REDIS_URL not set)
celery = Celery(
    broker=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://redis:6379/0"),
)

ALLOWED_MIME = {
    "application/pdf",
    "image/png", "image/jpeg", "image/webp", "image/tiff",
}

MAX_BYTES = 50 * 1024 * 1024  # 50 MB

@router.post("", summary="Upload a file to MinIO and register media asset")
async def upload(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File too large")

    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_MIME:
        raise HTTPException(status_code=415, detail=f"Unsupported content_type: {content_type}")

    digest = S3Service.sha256_bytes(data)
    key = f"{digest[:2]}/{digest}"

    s3 = get_s3()

    # Write to S3 if missing
    try:
        if not s3.object_exists(settings.s3_bucket, key):
            s3.put_bytes(settings.s3_bucket, key, data, content_type)
    except RuntimeError as e:
        # Surface clear 502 if MinIO is down/misconfigured
        raise HTTPException(status_code=502, detail=str(e))

    # Insert DB row (idempotent via sha256 unique)
    try:
        asset = MediaAsset(
            type=content_type,
            storage_uri=f"s3://{settings.s3_bucket}/{key}",
            sha256=digest,
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)
    except IntegrityError:
        db.rollback()
        asset = db.query(MediaAsset).filter_by(sha256=digest).first()
        if not asset:
            raise HTTPException(status_code=500, detail="Hash exists but row not found")

    # Auto-enqueue background extraction after we have a stable asset.id
    # We send request-id in headers for correlation; worker can read it if task is bound.
    req_id = request.headers.get("x-request-id")
    celery.send_task(
        "extract_metadata",
        args=[asset.id],
        headers={"request_id": req_id} if req_id else None,
    )

    
    return {"id": asset.id, "sha256": digest, "uri": asset.storage_uri}
