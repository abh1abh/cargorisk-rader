"""add freight tables

Revision ID: 244840b238d8
Revises: dd07e2692202
Create Date: 2025-10-22 08:53:22.568839

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = '244840b238d8'
down_revision: str | Sequence[str] | None = 'dd07e2692202'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_table(bind, name):
    return inspect(bind).has_table(name)

def _has_column(bind, table, col):
    insp = inspect(bind)
    cols = [c['name'] for c in insp.get_columns(table)]
    return col in cols

def upgrade():
    bind = op.get_bind()

    # 1) shipment_requests: create or alter
    if not _has_table(bind, "shipment_requests"):
        op.create_table(
            "shipment_requests",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("source_asset_id", sa.Integer, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
            sa.Column("status", sa.String, server_default="draft"),
            sa.Column("meta", JSONB, nullable=True)
        )
    else:
        # add columns if missing
        if not _has_column(bind, "shipment_requests", "source_asset_id"):
            op.add_column("shipment_requests", sa.Column("source_asset_id", sa.Integer, nullable=True))
        if not _has_column(bind, "shipment_requests", "updated_at"):
            op.add_column("shipment_requests", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")))
        if not _has_column(bind, "shipment_requests", "status"):
            op.add_column("shipment_requests", sa.Column("status", sa.String, server_default="draft"))
        # Your legacy column is named "metadata" (mapped as metadata_json in ORM). Keep it,
        # but prefer a new "meta" JSONB column going forward.
        if not _has_column(bind, "shipment_requests", "meta"):
            op.add_column("shipment_requests", sa.Column("meta", JSONB, nullable=True))

    # 2) freight_items (always new)
    if not _has_table(bind, "freight_items"):
        op.create_table(
            "freight_items",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("shipment_request_id", sa.Integer, sa.ForeignKey("shipment_requests.id", ondelete="CASCADE")),
            sa.Column("origin", sa.String),
            sa.Column("destination", sa.String),
            sa.Column("mode", sa.String),
            sa.Column("carrier", sa.String),
            sa.Column("equipment", sa.String),
            sa.Column("qty", sa.Integer),
            sa.Column("currency", sa.String),
            sa.Column("rate_per_unit", sa.Numeric(12,4)),
            sa.Column("total_freight", sa.Numeric(12,2)),
            sa.Column("valid_from", sa.Date()),
            sa.Column("valid_to", sa.Date()),
            sa.Column("confidence", sa.Float),
            sa.Column("raw_cells", JSONB),
        )

def downgrade():
    op.drop_table("freight_items")
    # Leave shipment_requests in place (it pre-existed in your codebase); only drop if you created it here.
    # If you want strict downgrade, uncomment next line:
    # op.drop_column("shipment_requests", "meta"); op.drop_column("shipment_requests", "status"); 
    # op.drop_column("shipment_requests", "updated_at"); op.drop_column("shipment_requests", "source_asset_id")