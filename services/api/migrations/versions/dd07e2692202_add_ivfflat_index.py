"""add ivfflat index

Revision ID: dd07e2692202
Revises: c83b761e773e
Create Date: 2025-10-17 09:49:08.464692

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dd07e2692202'
down_revision: Union[str, Sequence[str], None] = 'c83b761e773e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Ensure pgvector extension (safe if already installed)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")


    # 2) Drop any old indexes that use L2 or mismatched names/opclasses
    op.execute("DROP INDEX IF EXISTS idx_media_embedding;")               # your old ivfflat l2 index
    op.execute("DROP INDEX IF EXISTS media_assets_embedding_hnsw;")       # old HNSW L2 index

    # 3) Create IVF Flat (cosine) CONCURRENTLY in an autocommit block
    # Alembic must step out of the txn to use CONCURRENTLY.
    with op.get_context().autocommit_block():
        op.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS media_assets_embedding_ivf
            ON media_assets
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        """)

    # (Optional) Analyze so the planner gets fresh stats after index creation
    op.execute("ANALYZE media_assets;")



def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("DROP INDEX IF EXISTS media_assets_embedding_ivf;")

    # (Optional) Recreate prior indexes so down-revision still performs acceptably
    with op.get_context().autocommit_block():
        op.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS media_assets_embedding_hnsw
            ON media_assets
            USING hnsw (embedding vector_l2_ops);
        """)
