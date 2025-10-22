from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..core.deps import DocumentServiceDependency, get_db
from ..core.logging import get_logger
from ..schemas.document import DocumentOut, DocumentTextOut, OcrRunOut
from ..domain.exceptions import BadRequest, NotFound, ProcessingError, S3Unavailable

router = APIRouter(prefix="/document", tags=["document"])

log = get_logger("api.document")

@router.get("/{asset_id}", response_model=DocumentOut)
def get_document(
    asset_id: int,
    document_service: DocumentServiceDependency,
    db: Session = Depends(get_db),
):
    try:
        return document_service.get_document(db=db, asset_id=asset_id)
    except NotFound as e:
        raise HTTPException(404, "Not found") from e
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    except RuntimeError as e:
        raise HTTPException(500, "Unexpected server error.") from e


@router.get("/{asset_id}/text", response_model=DocumentTextOut)
def get_document_text(
    asset_id: int,
    document_service: DocumentServiceDependency,
    db: Session = Depends(get_db),
):
    try:
        return document_service.get_document_text(db=db, asset_id=asset_id)
    except NotFound as e:
        raise HTTPException(404, "Not found") from e
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    except RuntimeError as e:
        raise HTTPException(500, "Unexpected server error.") from e


@router.post("/{asset_id}/ocr", response_model=OcrRunOut)
def run_ocr(
    asset_id: int,
    document_service: DocumentServiceDependency,
    db: Session = Depends(get_db),
    lang: Annotated[str | None, Query(description="Tesseract language(s), e.g. 'eng+nor'")] = None,
):
    try:
        return document_service.run_ocr(db=db, asset_id=asset_id, lang=lang)
    except NotFound as e:
        raise HTTPException(404, "Not found") from e
    except S3Unavailable as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except ProcessingError as e:
        # mirrors previous 422 for OCR failures
        raise HTTPException(status_code=422, detail=str(e)) from e
    except BadRequest as e:
        raise HTTPException(400, str(e)) from e
    except RuntimeError as e:
        raise HTTPException(500, "Unexpected server error.") from e


@router.post("/{asset_id}/embed")
def embed_document(
    asset_id: int,
    document_service: DocumentServiceDependency,
    db: Session = Depends(get_db),
):
    try:
        return document_service.embed_document(db=db, asset_id=asset_id)
    except NotFound as e:
        raise HTTPException(404, "Asset not found") from e
    except ProcessingError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(500, "Unexpected server error.") from e


@router.get("/{asset_id}/download", include_in_schema=False)
def download_original(
    asset_id: int,
    document_service: DocumentServiceDependency,
    db: Session = Depends(get_db),
):
    try:
        url = document_service.generate_download_url(db=db, asset_id=asset_id)
        print
    except NotFound as e:
        raise HTTPException(status_code=404, detail="Document not found") from e
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return RedirectResponse(url, status_code=307)
