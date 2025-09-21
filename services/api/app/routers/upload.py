import os

from celery import Celery
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..core.deps import get_db, provide_s3, provide_default_bucket
from ..core.s3 import S3Service
from ..models import MediaAsset

router = APIRouter(prefix="/upload", tags=["upload"])

# Celery client (broker/backend default to local Redis if REDIS_URL not set)
celery = Celery(
    broker=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://redis:6379/0"),
)

ALLOWED_MIME = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/tiff",
}

MAX_BYTES = 50 * 1024 * 1024  # 50 MB


@router.post("", summary="Upload a file to MinIO and register media asset")
async def upload(
    request: Request, 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    s3: S3Service = Depends(provide_s3),
    bucket: str = Depends(provide_default_bucket),
):
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

    # Write to S3 if missing
    try:
        if not s3.object_exists(bucket, key):
            s3.put_bytes(bucket, key, data, content_type)
    except RuntimeError as e:
        # Surface clear 502 if MinIO is down/misconfigured
        raise HTTPException(status_code=502, detail=str(e)) from e
    # Insert DB row (idempotent via sha256 unique)
    try:
        asset = MediaAsset(
            type=content_type,
            storage_uri=f"s3://{bucket}/{key}",
            sha256=digest,
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)
    except IntegrityError as e:
        db.rollback()
        asset = db.query(MediaAsset).filter_by(sha256=digest).first()
        if not asset:
            raise HTTPException(status_code=500, detail="Hash exists but row not found") from e

    # Auto-enqueue background extraction after we have a stable asset.id
    # We send request-id in headers for correlation; worker can read it if task is bound.
    req_id = request.headers.get("x-request-id")
    celery.send_task(
        "extract_metadata",
        args=[asset.id],
        headers={"request_id": req_id} if req_id else None,
    )

    celery.send_task("ocr_asset", args=[asset.id])


    return {"id": asset.id, "sha256": digest, "uri": asset.storage_uri}
