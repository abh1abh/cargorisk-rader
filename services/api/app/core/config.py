from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str
    redis_url: str
    s3_endpoint: str
    s3_access_key: str
    s3_secret_key: str
    s3_bucket: str



    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",   # prevents the “Extra inputs are not permitted” error
    )


settings = Settings()
