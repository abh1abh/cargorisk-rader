from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from ..services.embedding_service import EmbeddingService
from ..services.ocr_service import OCRService
from ..services.s3_service import S3Service
from ..services.upload_service import UploadService
from .celery import get_celery
from .config import Settings, get_settings
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
    return S3Service(get_settings())
S3Dependency = Annotated[S3Service, Depends(provide_s3)]

def provide_default_bucket(settings: Settings = Depends(get_settings)) -> str:
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


def provide_upload_service(s3: S3Service = Depends(provide_s3), settings: Settings = Depends(get_settings), celery_app = Depends(get_celery)) -> UploadService:
    return UploadService(bucket=settings.s3_bucket, s3=s3, max_bytes=settings.max_upload_bytes, allowed_mime=settings.allowed_mime, celery_app=celery_app)
UploadServiceDependency = Annotated[UploadService, Depends(provide_upload_service)]