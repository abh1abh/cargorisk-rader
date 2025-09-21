import hashlib
import io

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError, EndpointConnectionError


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
        try:
            self._s3.put_object(Bucket=bucket, Key=key, Body=data, ContentType=content_type)
        except (ClientError, EndpointConnectionError) as e:
            raise RuntimeError(f"S3 put_object failed: {e}") from e

    def object_exists(self, bucket: str, key: str) -> bool:
        try:
            self._s3.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError as e:
            code = getattr(e, "response", {}).get("Error", {}).get("Code")
            if code in ("404", "NoSuchKey", "NotFound"):
                return False
            # Other errors (permissions, auth, etc.)
            raise RuntimeError(f"S3 head_object failed: {e}") from e
        except EndpointConnectionError as e:
            raise RuntimeError(f"S3 unreachable: {e}") from e

    def get_object_bytes(self, bucket: str, key: str) -> bytes:
        buf = io.BytesIO()
        try:
            self._s3.download_fileobj(bucket, key, buf)
        except (ClientError, EndpointConnectionError) as e:
            raise RuntimeError(f"S3 download_fileobj failed: {e}") from e
        return buf.getvalue()
    
    def get_uri_bytes(self, uri: str) -> bytes:
        assert uri.startswith("s3://"), f"Unexpected storage uri: {uri}"
        _, _, rest = uri.partition("s3://")
        bucket, _, key = rest.partition("/")
        return self.get_object_bytes(bucket, key)

    @staticmethod
    def sha256_bytes(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

