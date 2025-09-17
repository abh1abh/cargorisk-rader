import hashlib
import boto3
from botocore.client import Config
from .config import settings

class S3Service:
    def __init__(self, settings):
        # Path-style addressing is more MinIO-friendly
        self._s3 = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            config=Config(s3={"addressing_style": "path"}),
        )

    def put_bytes(self, bucket: str, key: str, data: bytes, content_type: str):
        self._s3.put_object(Bucket=bucket, Key=key, Body=data, ContentType=content_type)

    def object_exists(self, bucket: str, key: str) -> bool:
        try:
            self._s3.head_object(Bucket=bucket, Key=key)
            return True
        except Exception:
            return False
    
    @staticmethod
    def sha256_bytes(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

s3_service = S3Service(settings)