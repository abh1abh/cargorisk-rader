from __future__ import annotations

from dataclasses import dataclass

# from amqp import NotFound
from botocore.exceptions import ClientError, EndpointConnectionError
from sqlalchemy import update
from sqlalchemy.orm import Session

from ..core.logging import get_logger
from ..core.metrics import timed
from ..domain.exceptions import NotFound, ProcessingError, S3Unavailable
from ..domain.ports import BlobStore, EmbeddingModelPort, OcrPort
from ..models import MediaAsset
from ..schemas.document import DocumentOut, DocumentTextOut, OcrRunOut

log = get_logger("svc.document")

# TODO: Create DB repo for document

@dataclass(slots=True)
class DocumentService:
    ocr: OcrPort
    embedder: EmbeddingModelPort
    s3: BlobStore
    s3_public_base: str
    
    # Public 
    def get_document(self, db: Session, asset_id: int) -> DocumentOut:
        m = self._get_asset(db, asset_id)
        return DocumentOut(
            id=m.id, type=m.type, storage_uri=m.storage_uri, has_text=bool(m.ocr_text)
        )

    def get_document_text(self, db: Session, asset_id: int) -> DocumentTextOut:
        m = self._get_asset(db, asset_id)
        return DocumentTextOut(id=m.id, text=m.ocr_text or "")
    
    def run_ocr(self, db: Session, asset_id: int, lang: str | None) -> OcrRunOut:
        t = timed("ocr")
        m = self._get_asset(db, asset_id)

        log.info("ocr_start", extra={"asset_id": asset_id, "mime": m.type})
        try:
            blob = self.s3.get_uri_bytes(m.storage_uri)
        except (ClientError, EndpointConnectionError) as e:
            log.warning("s3_error", extra={"asset_id": asset_id, "error": e})
            raise S3Unavailable(f"S3 error: {e}") from e

        try:
            mime = m.type or ""
            eff_lang = lang or "eng+nor"
            if mime.startswith("image/"):
                text = self.ocr.image_bytes_to_text(blob, lang=eff_lang)
                mode = "image"
            elif mime == "application/pdf":
                text = self.ocr.pdf_bytes_to_text(blob, lang=eff_lang)
                mode = "pdf"
            elif mime in {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/vnd.ms-excel.sheet.macroEnabled.12",
            }:
                text = self.ocr.xlsx_bytes_to_text(blob)
                mode = "xlsx"
            else:
                # Try PDF first, then image, as fallbacks
                try:
                    text = self.ocr.pdf_bytes_to_text(blob)
                    mode = "pdf_fallback"
                except Exception:
                    text = self.ocr.image_bytes_to_text(blob)
                    mode = "image_fallback"
        except Exception as e:
            log.error("ocr_failed", extra={"asset_id": asset_id, "error": e})
            raise ProcessingError(f"OCR failed: {e}") from e

        m.ocr_text = text
        db.commit()

        t({"asset_id": asset_id})
        log.info("ocr_done", extra={"asset_id": asset_id, "chars": len(text or ""), "mode": mode})
        return OcrRunOut(id=m.id, ocr_chars=len(text or ""))
    
    def embed_document(self, db: Session, asset_id: int) -> dict:
        t = timed("embed")
        m = self._get_asset(db, asset_id)
        text = m.ocr_text or ""

        try:
            emb = self.embedder.embed_text(text)
        except Exception as e:
            log.error("embed_failed", extra={"asset_id": asset_id, "error": e})
            raise ProcessingError(f"Embedding failed: {e}") from e

        # Use UPDATE to avoid loading large vector back into ORM if undesired
        db.execute(update(MediaAsset).where(MediaAsset.id == asset_id).values(embedding=emb))
        db.commit()

        t({"asset_id": asset_id, "chars": len(text), "dim": len(emb)})
        return {"id": m.id, "dim": len(emb)}

    def generate_download_url(self, db: Session, asset_id: int) -> str:
        m = self._get_asset(db, asset_id)
        if not m.storage_uri:
            raise NotFound("Document not found")
        bucket, key = self.s3.parse_s3_uri(m.storage_uri)
        try:
            url = self.s3.generate_presigned_url(
                "get_object",
                params={"Bucket": bucket, "Key": key},
                expires_in=600,
            )
        except Exception as e:
            log.error("presign_failed", extra={"asset_id": asset_id, "error": e})
            # Infrastructure-ish failure
            raise RuntimeError(str(e)) from e

        # Normalize to public base if needed
        url = url.replace("http://minio:9000", self.s3_public_base)
        return url
    
    # Internal
    @staticmethod
    def _get_asset(db: Session, asset_id: int) -> MediaAsset:
        m = db.get(MediaAsset, asset_id)
        if not m:
            raise NotFound("Not found")
        return m