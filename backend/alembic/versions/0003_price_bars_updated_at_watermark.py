"""0003 price bars updated_at watermark + composite index

Revision ID: 0003_price_bars_updated_at_watermark
Revises: 0002_symbols_ingestion_audit_proposals
Create Date: 2026-02-25
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_price_bars_updated_at_watermark"
down_revision = "0002_symbols_ingestion_audit_proposals"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column(
        "price_bars",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.execute("DROP INDEX IF EXISTS ix_price_bars_updated_at")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_price_bars_ticker_updated_at_desc "
        "ON price_bars (ticker, updated_at DESC)"
    )

def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_price_bars_ticker_updated_at_desc")
    op.execute("CREATE INDEX IF NOT EXISTS ix_price_bars_updated_at ON price_bars (updated_at)")
    op.drop_column("price_bars", "updated_at")
