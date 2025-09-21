"""change embedding to 384 dims

Revision ID: c83b761e773e
Revises: 4456b52566cc
Create Date: 2025-09-21 17:06:54.038515

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c83b761e773e'
down_revision: Union[str, Sequence[str], None] = '4456b52566cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE media_assets ALTER COLUMN embedding TYPE vector(384);")



def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE media_assets ALTER COLUMN embedding TYPE vector(768);")

