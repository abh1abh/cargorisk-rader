from typing import Annotated

from botocore.exceptions import ClientError, EndpointConnectionError
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..core.deps import get_db, provide_s3
from ..core.logging import get_logger, now_ms
from ..core.s3 import S3Service
from ..models import MediaAsset
from ..schemas.documents import DocumentOut, DocumentTextOut, OcrRunOut
from ..services import ocr as ocrsvc
from ..services.embeddings import embed_text

router = APIRouter(prefix="/documents", tags=["documents"])

log = get_logger("api.documents")


@router.get("/{asset_id}", response_model=DocumentOut)
def get_document(asset_id: int, db: Session = Depends(get_db)):
    m = db.get(MediaAsset, asset_id)
    if not m:
        raise HTTPException(404, "Not found")
    return DocumentOut(
        id=m.id, type=m.type, storage_uri=m.storage_uri, has_text=bool(m.ocr_text)
    )

@router.get("/{asset_id}/text", response_model=DocumentTextOut)
def get_document_text(asset_id: int, db: Session = Depends(get_db)):
    m = db.get(MediaAsset, asset_id)
    if not m:
        raise HTTPException(404, "Not found")
    return DocumentTextOut(id=m.id, text=m.ocr_text or "")


@router.post("/{asset_id}/ocr", response_model=OcrRunOut)
def run_ocr(
    asset_id: int, 
    s3: S3Service = Depends(provide_s3), 
    db: Session = Depends(get_db),
    lang: Annotated[str | None, Query(description="Tesseract language(s), e.g. 'eng+nor'")] = None,

):
    t0 = now_ms()
    m = db.get(MediaAsset, asset_id)
    if not m:
        raise HTTPException(404, "Not found")
    
    log.info("ocr_start", extra={"asset_id": asset_id, "mime": m.type})

    try:
        blob = s3.get_uri_bytes(m.storage_uri)
    except (ClientError, EndpointConnectionError) as e:
        log.warning("s3_error", extra={"asset_id": asset_id, "error": e.__class__.__name__})
        raise HTTPException(status_code=502, detail=f"S3 error: {e.__class__.__name__}") from e
    try:
        if (m.type or "").startswith("image/"):
            text = ocrsvc.image_bytes_to_text(blob, lang=lang or "eng+nor")
            mode = "image"
        elif m.type == "application/pdf":
            text = ocrsvc.pdf_bytes_to_text(blob, lang=lang or "eng+nor")
            mode = "pdf"
        else:
            try:
                text = ocrsvc.pdf_bytes_to_text(blob)
                mode = "pdf_fallback"
            except Exception:
                text = ocrsvc.image_bytes_to_text(blob)
                mode = "image_fallback"
    except Exception as e:
        log.error("ocr_failed", extra={"asset_id": asset_id, "error": e.__class__.__name__})
        raise HTTPException(status_code=422, detail=f"OCR failed: {e.__class__.__name__}") from e

    m.ocr_text = text
    db.commit()
    dt = round(now_ms() - t0, 2)

    log.info("ocr_done", extra={"asset_id": asset_id, "chars": len(text or ""), "ms": dt, "mode": mode})
    return OcrRunOut(id=m.id, ocr_chars=len(text or ""))

# @router.post("/{asset_id}/embed")
# def embed_document(asset_id: int, db: Session = Depends(get_db)):
#     m = db.get(MediaAsset, asset_id)
#     if not m:
#         raise HTTPException(404, "Asset not found")
#     text = m.ocr_text or ""
#     emb = embed_text(text)
#     db.execute(update(MediaAsset).where(MediaAsset.id==asset_id).values(embedding=emb))
#     db.commit()
#     return {"id": m.id, "dim": len(emb)}