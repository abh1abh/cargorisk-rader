from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from ..domain.ports import BlobStore, EmbeddingModelPort, MediaAssetRepo, OcrPort, MediaAssetRepo
from ..infra.embedding_model import EmbeddingModel
from ..infra.ocr_engine import OcrEngine
from ..infra.s3_blob_store import S3BlobStore
from ..infra.sqlalchemy_media_asset_repo import SqlAlchemyMediaAssetRepo
from ..services.document_service import DocumentService
from ..services.search_service import SearchService
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

@lru_cache(maxsize=1)
def _s3_singleton() -> BlobStore:
    return S3BlobStore(get_settings())  # zero-arg, safe to cache

def provide_s3() -> BlobStore:
    return _s3_singleton()  # dependency-safe wrapper
S3Dependency = Annotated[BlobStore, Depends(provide_s3)]

def provide_default_bucket(settings: Settings = Depends(get_settings)) -> str: 
    return settings.s3_bucket

@lru_cache(maxsize=1)
def get_ocr_service() -> OcrPort:
    return OcrEngine()
OCRDependency = Annotated[OcrPort, Depends(get_ocr_service)]

@lru_cache(maxsize=1)
def get_embedding_model() -> EmbeddingModelPort:
    # Create one shared instance (lazy-loaded model)
    return EmbeddingModel()
EmbeddingDependency = Annotated[EmbeddingModelPort, Depends(get_embedding_model)]

@lru_cache(maxsize=1)
def get_media_asset_repo() -> MediaAssetRepo:
    return SqlAlchemyMediaAssetRepo()
MediaAssetRepoDependency = Annotated[MediaAssetRepo, Depends(get_media_asset_repo)]


def provide_upload_service(
    s3: BlobStore = Depends(provide_s3), 
    settings: Settings = Depends(get_settings), 
    celery_app = Depends(get_celery),
    media_asset_repo: MediaAssetRepo = Depends(get_media_asset_repo)
) -> UploadService:
        return UploadService(bucket=settings.s3_bucket, s3=s3, max_bytes=settings.max_upload_bytes, allowed_mime=settings.allowed_mime, celery_app=celery_app, media_asset_repo=media_asset_repo)
UploadServiceDependency = Annotated[UploadService, Depends(provide_upload_service)]

@lru_cache(maxsize=1)
def _document_singleton() -> DocumentService:
    # uses cached singletons directly, no Depends()
    s3 = _s3_singleton()
    ocr = get_ocr_service()
    embedder = get_embedding_model()
    settings = get_settings()
    media_asset_repo = get_media_asset_repo()
    return DocumentService(s3=s3, ocr=ocr, embedder=embedder, s3_public_base=settings.s3_public_base, media_asset_repo=media_asset_repo)

def provide_document_service() -> DocumentService:
    # this one is exposed to FastAPI
    return _document_singleton()

DocumentServiceDependency = Annotated[DocumentService, Depends(provide_document_service)]


@lru_cache(maxsize=1)
def _search_singleton() -> SearchService:
    embedder = get_embedding_model()
    settings = get_settings()
    embed_dim = getattr(settings, "embed_dim", 384)
    probes = getattr(settings, "ivfflat_probes", 20)
    return SearchService(embedder=embedder, embed_dim=embed_dim, ivfflat_probes=probes)

def provide_search_service() -> SearchService:
    return _search_singleton()

SearchServiceDependency = Annotated[SearchService, Depends(provide_search_service)]


