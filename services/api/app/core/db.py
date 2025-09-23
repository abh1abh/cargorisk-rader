from pgvector.psycopg import register_vector
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

dsn = (
    "postgresql+psycopg://"
    f"{settings.postgres_user}:{settings.postgres_password}"
    f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
)

engine = create_engine(dsn, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()


# Ensures psycopg understands pgvector on each new connection
@event.listens_for(engine, "connect")
def _register_vector(dbapi_connection, connection_record):
    register_vector(dbapi_connection)