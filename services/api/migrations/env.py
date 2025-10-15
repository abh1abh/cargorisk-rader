# services/api/migrations/env.py
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import URL

# add the project root (/app), not /app/app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import get_settings
from app.core.db import Base

config = context.config
target_metadata = Base.metadata
fileConfig(config.config_file_name)


def get_url():
    s = get_settings()
    return URL.create(
        drivername="postgresql+psycopg",
        username=s.postgres_user,
        password=s.postgres_password.get_secret_value(),
        host=s.postgres_host,
        port=s.postgres_port,
        database=s.postgres_db,
    )

def run_migrations_offline():
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        {"sqlalchemy.url": get_url()},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
