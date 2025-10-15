from __future__ import annotations

from functools import lru_cache

from pgvector.psycopg import register_vector
from sqlalchemy import create_engine, event
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import get_settings


@lru_cache(maxsize=1)
def get_engine():
    settings = get_settings()
    url = URL.create(
        drivername="postgresql+psycopg",
        username=settings.postgres_user,
        password=settings.postgres_password.get_secret_value(),  # SecretStr -> str
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=settings.postgres_db,
    )
    engine = create_engine(url, pool_pre_ping=True, future=True)

    # Ensure pgvector is registered on each new connection
    @event.listens_for(engine, "connect")
    def _register_vector(dbapi_connection, connection_record):
        register_vector(dbapi_connection)

    return engine

Engine = get_engine()
SessionLocal = sessionmaker(bind=Engine, autocommit=False, autoflush=False, future=True)
Base = declarative_base()
