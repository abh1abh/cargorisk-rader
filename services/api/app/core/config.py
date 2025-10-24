from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
     # Postgres 
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(alias="POSTGRES_DB")
    postgres_user: str = Field(alias="POSTGRES_USER")
    postgres_password: SecretStr = Field(alias="POSTGRES_PASSWORD")

    # Redis / Celery 
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")

    # S3 / MinIO 
    s3_endpoint: str = Field(default="http://minio:9000", alias="S3_ENDPOINT")
    s3_access_key: SecretStr = Field(alias="S3_ACCESS_KEY")
    s3_secret_key: SecretStr = Field(alias="S3_SECRET_KEY")
    s3_bucket: str = Field(default="uploads", alias="S3_BUCKET")
    s3_public_base: str = Field(default="http://localhost:9000", alias="S3_PUBLIC_BASE")

   # Upload policy
    max_upload_bytes: int = Field(default=50 * 1024 * 1024, alias="MAX_UPLOAD_BYTES")
    allowed_mime: set[str] = Field(
        default={
            "application/pdf",
            "image/png",
            "image/jpeg",
            "image/webp",
            "image/tiff",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel.sheet.macroEnabled.12",
            "text/csv",
        },
        alias="ALLOWED_MIME",
    )

     # Hugging Face - Freight Extractor 
    hf_base_url: str = Field(
        default="https://router.huggingface.co/v1",
        alias="HF_BASE_URL",
    )
    hf_api_key: str = Field(default="", alias="HF_API_KEY")
    freight_extractor_mode: str = Field(default="hybrid", alias="FREIGHT_EXTRACTOR")  # llm|heuristic|hybrid


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",   # prevents the “Extra inputs are not permitted” error
    )


@lru_cache
def get_settings() -> Settings:
    # Cached across the app lifetime; still overrideable in tests
    return Settings()