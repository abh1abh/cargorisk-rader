from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from sqlalchemy.exc import IntegrityError
from ..core.db import SessionLocal
from ..models import MediaAsset
from ..core.s3 import s3_service, S3Service
from ..core.config import settings
from ..core.deps import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/upload", tags=["upload"])

ALLOWED_MIME = {"application/pdf", "image/png", "image/jpeg", "image/webp", "image/tiff"}

@router.post("", summary="Upload a file to MinIO and register media asset")
async def upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # 1) Read bytes (for large files, consider chunked streaming)
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    # 2) MIME (trust client or sniff)
    content_type = file.content_type or "application/octet-stream"
    # Simple allowlist (optional; relax for dev)
    if content_type not in ALLOWED_MIME:
        # allow pdf/images only
        raise HTTPException(status_code=415, detail=f"Unsupported content_type: {content_type}")

    # 3) Hash & deterministic key
    digest = S3Service.sha256_bytes(data)
    key = f"{digest[:2]}/{digest}"  # 256-way sharding under bucket

    # 4) Put to S3 if new (idempotent by content hash)
    if not s3_service.object_exists(settings.s3_bucket, key):
        s3_service.put_bytes(settings.s3_bucket, key, data, content_type)

    # 5) Insert DB row (idempotent via sha256 unique)
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
        # Row already exists; fetch it and return
        asset = db.query(MediaAsset).filter_by(sha256=digest).first()
        if not asset:
            raise HTTPException(status_code=500, detail="Hash exists but row not found")

    return {"id": asset.id, "sha256": digest, "uri": asset.storage_uri}
