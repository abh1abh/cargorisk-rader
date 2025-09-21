from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import update
from sqlalchemy.orm import Session
from ..models import MediaAsset
from ..services import ocr as ocrsvc
from ..schemas.documents import DocumentOut, DocumentTextOut, OcrRunOut
from ..core.deps import provide_s3, get_db
from ..core.s3 import S3Service
from botocore.exceptions import ClientError, EndpointConnectionError
from typing import Annotated
from fastapi import Query


router = APIRouter(prefix="/documents", tags=["documents"])

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
    m = db.get(MediaAsset, asset_id)
    if not m:
        raise HTTPException(404, "Not found")
    try:
        blob = s3.get_uri_bytes(m.storage_uri)
    except (ClientError, EndpointConnectionError) as e:
        raise HTTPException(status_code=502, detail=f"S3 error: {e.__class__.__name__}") from e
    try:
        if (m.type or "").startswith("image/"):
            text = ocrsvc.image_bytes_to_text(blob, lang=lang or "eng+nor")
        elif m.type == "application/pdf":
            text = ocrsvc.pdf_bytes_to_text(blob, lang=lang or "eng+nor")
        else:
            try:
                text = ocrsvc.pdf_bytes_to_text(blob)
            except Exception:
                text = ocrsvc.image_bytes_to_text(blob)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"OCR failed: {e.__class__.__name__}") from e

    m.ocr_text = text              # simpler than Core update(...)
    db.commit()
    return OcrRunOut(id=m.id, ocr_chars=len(text or ""))