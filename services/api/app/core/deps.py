# services/api/app/core/deps.py
from .db import SessionLocal
from .s3 import S3Service
from .config import settings


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


_s3_singleton: S3Service | None = None

def provide_s3() -> S3Service:
    global _s3_singleton
    if _s3_singleton is None:
        _s3_singleton = S3Service(settings)
    return _s3_singleton

def provide_default_bucket() -> str:
    return settings.s3_bucket
