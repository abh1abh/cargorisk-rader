"""change embedding to 384 dims

Revision ID: c83b761e773e
Revises: 4456b52566cc
Create Date: 2025-09-21 17:06:54.038515

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c83b761e773e'
down_revision: str | Sequence[str] | None = '4456b52566cc'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Adjust column dimension 
    op.execute("ALTER TABLE media_assets ALTER COLUMN embedding TYPE vector(384);")

    # Add index for fast search
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_media_embedding
        ON media_assets
        USING ivfflat (embedding vector_l2_ops)
        WITH (lists = 100);
    """)




def downgrade() -> None:
    """Downgrade schema."""
    # Revert to 768 dim vector
    op.execute("ALTER TABLE media_assets ALTER COLUMN embedding TYPE vector(768);")

    # Drop index first
    op.execute("DROP INDEX IF EXISTS idx_media_embedding;")
