import os

from celery import Celery, chain
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..core.deps import S3Dependency, get_db, provide_default_bucket
from ..core.logging import get_logger, now_ms, request_id_ctx
from ..models import MediaAsset
from ..services.s3 import S3Service

log = get_logger("api.upload")


router = APIRouter(prefix="/upload", tags=["upload"])

# Celery client (broker/backend default to local Redis if REDIS_URL not set)
celery = Celery(
    broker=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://redis:6379/0"),
)

# add to ALLOWED_MIME
ALLOWED_MIME = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/tiff",
    # spreadsheets
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "application/vnd.ms-excel.sheet.macroEnabled.12",    
    "text/csv",  # optional
}


MAX_BYTES = 50 * 1024 * 1024  # 50 MB


@router.post("", summary="Upload a file to MinIO and register media asset")
async def upload(
    s3: S3Dependency,
    request: Request, 
    db: Session = Depends(get_db),
    bucket: str = Depends(provide_default_bucket),
    file: UploadFile = File(...), 
):
    t0 = now_ms()

    data = await file.read()
    size = len(data or b"")
    content_type = file.content_type or "application/octet-stream"
    log.info("upload_start", extra={"mime": content_type, "bytes": size})

    if not data:
        log.warning("upload_empty")
        raise HTTPException(status_code=400, detail="Empty file")
    if len(data) > MAX_BYTES:
        log.warning("upload_too_large", extra={"bytes": size, "max": MAX_BYTES})
        raise HTTPException(status_code=413, detail="File too large")

    if content_type not in ALLOWED_MIME:
        log.warning("upload_unsupported_mime", extra={"mime": content_type})
        raise HTTPException(status_code=415, detail=f"Unsupported content_type: {content_type}")

    digest = S3Service.sha256_bytes(data)
    key = f"{digest[:2]}/{digest}"

    # Write to S3 if missing
    try:
        existed = s3.object_exists(bucket, key)
        if not existed:
            s3.put_bytes(bucket, key, data, content_type)
        log.info("upload_s3", extra={"bucket": bucket, "key": key, "dedup": existed})

    except RuntimeError as e:
        # Surface clear 502 if MinIO is down/misconfigured
        log.error("upload_s3_error", extra={"error": str(e)})
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
        row_created = True
    except IntegrityError as e:
        db.rollback()
        asset = db.query(MediaAsset).filter_by(sha256=digest).first()
        if not asset:
            log.error("upload_db_inconsistent", extra={"sha256": digest})
            raise HTTPException(status_code=500, detail="Hash exists but row not found") from e
        row_created = False

    log.info("upload_db", extra={"asset_id": asset.id, "sha256": digest, "row_created": row_created})

    # Auto-enqueue background extraction after we have a stable asset.id
    # We send request-id in headers for correlation; worker can read it if task is bound.
    req_id = request_id_ctx.get()          # <-- instead of request.headers.get("x-request-id")
    headers = {"request_id": req_id} 

    # Keep extract_metadata in parallel (optional), but chain OCR -> EMBED
    celery.send_task("extract_metadata", args=[asset.id], headers=headers)

    # Ensure the worker has tasks named ocr_asset and embed_asset
    workflow = chain(
        celery.signature("ocr_asset", args=[asset.id], headers=headers),
        celery.signature("embed_asset", args=[asset.id], headers=headers, immutable=True),
    )   
    workflow.apply_async()

    dt = round(now_ms() - t0, 2)
    log.info("upload_done", extra={"asset_id": asset.id, "ms": dt})

    return {"id": asset.id, "sha256": digest, "uri": asset.storage_uri}
