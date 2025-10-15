
from collections.abc import Iterable

from celery import Celery, chain
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..core.logging import get_logger, request_id_ctx
from ..core.metrics import timed
from ..models import MediaAsset
from .s3_service import S3Service

log = get_logger("svc.upload")


class UploadService:
    def __init__(self, bucket: str, s3: S3Service, max_bytes: int, allowed_mime: Iterable[str], celery_app: Celery):
        self.s3 = s3
        self.bucket = bucket
        self.max_bytes = max_bytes
        self.allowed_mime = set(allowed_mime)
        self.celery_app = celery_app

    # Public methods
    async def upload(self, db: Session, file) -> dict:
        t = timed("upload")
        data = await file.read()
        size = len(data or b"")
        content_type = file.content_type or "application/octet-stream"
        log.info("upload_start", extra={"mime": content_type, "bytes": size})

        self._validate_file(size=size, content_type=content_type)

        digest = S3Service.sha256_bytes(data)
        key = f"{digest[:2]}/{digest}"

        # Write to S3 if missing
        try:
            existed = self.s3.object_exists(self.bucket, key)
            if not existed:
                self.s3.put_bytes(self.bucket, key, data, content_type)
            log.info("upload_s3", extra={"bucket": self.bucket, "key": key, "dedup": existed})

        except RuntimeError as e:
            # Surface clear 502 if MinIO is down/misconfigured
            log.error("upload_s3_error", extra={"error": str(e)})
            raise RuntimeError("S3 upload failed") from e
        # Insert DB row (idempotent via sha256 unique)
        try:
            asset = MediaAsset(
                type=content_type,
                storage_uri=f"s3://{self.bucket}/{key}",
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
                # Convert to runtime (infra/state) error; don't raise IntegrityError yourself
                log.warning("upload_db_dedup", extra={"asset_id": asset.id, "sha256": digest})
                row_created = False
                raise RuntimeError("DB inconsistent: hash exists but row not found") from e
        # duplicate is fine; continue
        except Exception as e:
            row_created = False
            db.rollback()
            log.error("upload_db_error", extra={"error": str(e)})
            raise RuntimeError("DB operation failed") from e

        log.info("upload_db", extra={"asset_id": asset.id, "sha256": digest, "row_created": row_created})

        # Enqueue background processing (OCR, embed) if new row       
        try:
            self._enqueue_pipeline(asset.id)
        except Exception as e:
            log.error("upload_enqueue_error", extra={"asset_id": asset.id, "error": str(e)})
            raise RuntimeError("Enqueue failed") from e

        ms = t({"asset_id": asset.id})

        log.info("upload_done", extra={"asset_id": asset.id, "ms": ms})

        return {"id": asset.id, "sha256": digest, "uri": asset.storage_uri}


    # Internal methods
    def _validate_file(self, size: int, content_type: str) -> None:
        if size == 0:
            raise ValueError("Empty file")
        if size > self.max_bytes:
            raise ValueError("File too large")
        if content_type not in self.allowed_mime:
            raise ValueError(f"Unsupported content_type: {content_type}")

    def _enqueue_pipeline(self, asset_id: int) -> None:
        # Auto-enqueue background extraction after we have a stable asset.id
        # We send request-id in headers for correlation; worker can read it if task is bound.
        headers = {"request_id": request_id_ctx.get()}
        try:
            # Keep extract_metadata in parallel (optional), but chain OCR -> EMBED
            self.celery_app.send_task("extract_metadata", args=[asset_id], headers=headers)
            chain(
                self.celery_app.signature("ocr_asset", args=[asset_id], headers=headers),
                self.celery_app.signature("embed_asset", args=[asset_id], headers=headers, immutable=True),
            ).apply_async()
        except Exception as e:
            log.warning("enqueue_failed", extra={"asset_id": asset_id, "error": e.__class__.__name__})
            raise RuntimeError("Failed to enqueue background work") from e