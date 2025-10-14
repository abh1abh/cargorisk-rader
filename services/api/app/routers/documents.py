from typing import Annotated

from botocore.exceptions import ClientError, EndpointConnectionError
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import update
from sqlalchemy.orm import Session

from ..core.deps import get_db, provide_s3
from ..core.logging import get_logger, now_ms
from ..core.s3 import S3Service
from ..models import MediaAsset
from ..schemas.documents import DocumentOut, DocumentTextOut, OcrRunOut
from ..services import ocr as ocrsvc
from ..services.embeddings import embed_text
from ..core.metrics import timed

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
    time = timed("ocr")
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
        mime = m.type or ""

        if mime.startswith("image/"):
            text = ocrsvc.image_bytes_to_text(blob, lang=lang or "eng+nor")
            mode = "image"
        elif mime == "application/pdf":
            text = ocrsvc.pdf_bytes_to_text(blob, lang=lang or "eng+nor")
            mode = "pdf"
        elif mime in {
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
            "application/vnd.ms-excel.sheet.macroEnabled.12",  # .xlsm
            }:
            text = ocrsvc.xlsx_bytes_to_text(blob)
            mode = "xlsx"
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
    ms = time({"asset_id": asset_id})

    log.info("ocr_done", extra={"asset_id": asset_id, "chars": len(text or ""), "mode": mode})
    return OcrRunOut(id=m.id, ocr_chars=len(text or ""))

@router.post("/{asset_id}/embed")
def embed_document(asset_id: int, db: Session = Depends(get_db)):
    time = timed("embed")
    m = db.get(MediaAsset, asset_id)
    if not m:
        raise HTTPException(404, "Asset not found")
    text = m.ocr_text or ""
    emb = embed_text(text)
    db.execute(update(MediaAsset).where(MediaAsset.id==asset_id).values(embedding=emb))
    db.commit()
    ms = time({"asset_id": asset_id, "chars": len(text), "dim": len(emb)})
    return {"id": m.id, "dim": len(emb)}

@router.get("/{id}/download", include_in_schema=False)
def download_original(id: int, s3: S3Service = Depends(provide_s3), db: Session = Depends(get_db)):
    media_asset = db.get(MediaAsset, id)
    if not media_asset or not media_asset.storage_uri:
        raise HTTPException(status_code=404, detail="Document not found")
    print("HEARRRR")
    bucket, key = s3.parse_s3_uri(media_asset.storage_uri)
    print(bucket, key)

    try:
        url = s3.generate_presigned_url(
            "get_object",
            params={
                "Bucket": bucket,
                "Key": key,
                # Optional: force inline view + content type if PDFs
                # "ResponseContentDisposition": "inline",
                # "ResponseContentType": "application/pdf",
            },
            expires_in=600,  # 10 minutes
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    public_base = "http://localhost:9000"  # or settings.s3_public_endpoint
    url = url.replace("http://minio:9000", public_base)
    # 307 so browsers follow with GET
    return RedirectResponse(url, status_code=307)