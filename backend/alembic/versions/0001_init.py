"""0001_init

Revision ID: 0001_init
Revises: 
Create Date: 2026-02-25
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # clients
    op.create_table(
        "clients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_clients_owner_user_id", "clients", ["owner_user_id"])

    # portfolios
    op.create_table(
        "portfolios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("base_ccy", sa.String(8), server_default="USD", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_portfolios_client_id", "portfolios", ["client_id"])

    # positions
    op.create_table(
        "positions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("portfolio_id", sa.Integer(), sa.ForeignKey("portfolios.id"), nullable=False),
        sa.Column("ticker", sa.String(24), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("kind", sa.String(16), server_default="asset", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_positions_portfolio_id", "positions", ["portfolio_id"])
    op.create_index("ix_positions_ticker", "positions", ["ticker"])
    op.create_unique_constraint("uq_position_portfolio_ticker", "positions", ["portfolio_id", "ticker"])

    # price_bars
    op.create_table(
        "price_bars",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticker", sa.String(24), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("close", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_price_bars_ticker", "price_bars", ["ticker"])
    op.create_index("ix_price_bars_ts", "price_bars", ["ts"])
    op.create_unique_constraint("uq_price_ticker_ts", "price_bars", ["ticker", "ts"])

def downgrade():
    op.drop_table("price_bars")
    op.drop_table("positions")
    op.drop_table("portfolios")
    op.drop_table("clients")
    op.drop_table("users")
