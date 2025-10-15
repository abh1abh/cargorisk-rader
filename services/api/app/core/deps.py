from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from ..services.embeddings import EmbeddingService
from ..services.ocr import OCRService
from ..services.s3 import S3Service
from .config import settings
from .db import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def provide_s3() -> S3Service:
    return _s3_singleton()

@lru_cache(maxsize=1)
def _s3_singleton() -> S3Service:
    return S3Service(settings)
S3Dependency = Annotated[S3Service, Depends(provide_s3)]

def provide_default_bucket() -> str:
    return settings.s3_bucket

@lru_cache(maxsize=1)
def get_ocr_service() -> OCRService:
    return OCRService()
OCRDependency = Annotated[OCRService, Depends(get_ocr_service)]

@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    # Create one shared instance (lazy-loaded model)
    return EmbeddingService()
EmbeddingDependency = Annotated[EmbeddingService, Depends(get_embedding_service)]