"""0002 symbols ingestion audit proposals

Revision ID: 0002_symbols_ingestion_audit_proposals
Revises: 0001_init
Create Date: 2026-02-25
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_symbols_ingestion_audit_proposals"
down_revision = "0001_init"
branch_labels = None
depends_on = None

def upgrade():
    # symbols
    op.create_table(
        "symbols",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticker", sa.String(24), nullable=False),
        sa.Column("cik", sa.String(16), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("exchange", sa.String(32), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
    )
    op.create_index("ix_symbols_ticker", "symbols", ["ticker"])
    op.create_index("ix_symbols_cik", "symbols", ["cik"])
    op.create_unique_constraint("uq_symbols_ticker", "symbols", ["ticker"])

    # series_observations
    op.create_table(
        "series_observations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("series_code", sa.String(128), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("meta", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_series_observations_source", "series_observations", ["source"])
    op.create_index("ix_series_observations_series_code", "series_observations", ["series_code"])
    op.create_index("ix_series_observations_ts", "series_observations", ["ts"])
    op.create_unique_constraint("uq_series_source_code_ts", "series_observations", ["source", "series_code", "ts"])

    # filing_facts
    op.create_table(
        "filing_facts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cik", sa.String(16), nullable=False),
        sa.Column("taxonomy", sa.String(32), nullable=False),
        sa.Column("tag", sa.String(128), nullable=False),
        sa.Column("unit", sa.String(32), nullable=False),
        sa.Column("end", sa.String(16), nullable=False),
        sa.Column("fy", sa.Integer(), nullable=True),
        sa.Column("fp", sa.String(8), nullable=True),
        sa.Column("val", sa.Float(), nullable=False),
        sa.Column("accn", sa.String(32), nullable=True),
        sa.Column("filed", sa.String(16), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_filing_facts_cik", "filing_facts", ["cik"])
    op.create_unique_constraint("uq_fact_key", "filing_facts", ["cik", "taxonomy", "tag", "unit", "end", "fy", "fp"])

    # audit_events
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_audit_events_user_id", "audit_events", ["user_id"])
    op.create_index("ix_audit_events_action", "audit_events", ["action"])
    op.create_index("ix_audit_events_entity_type", "audit_events", ["entity_type"])
    op.create_index("ix_audit_events_entity_id", "audit_events", ["entity_id"])

    # proposal_runs
    op.create_table(
        "proposal_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("portfolio_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("inputs_hash", sa.String(64), nullable=False),
        sa.Column("assumptions", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_proposal_runs_portfolio_id", "proposal_runs", ["portfolio_id"])
    op.create_index("ix_proposal_runs_user_id", "proposal_runs", ["user_id"])
    op.create_index("ix_proposal_runs_as_of", "proposal_runs", ["as_of"])
    op.create_index("ix_proposal_runs_inputs_hash", "proposal_runs", ["inputs_hash"])

    # proposal_artifacts
    op.create_table(
        "proposal_artifacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("proposal_run_id", sa.Integer(), nullable=False),
        sa.Column("mime", sa.String(64), nullable=False),
        sa.Column("filename", sa.String(256), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_proposal_artifacts_proposal_run_id", "proposal_artifacts", ["proposal_run_id"])
    op.create_unique_constraint("uq_artifact_run", "proposal_artifacts", ["proposal_run_id"])

def downgrade():
    op.drop_constraint("uq_artifact_run", "proposal_artifacts")
    op.drop_index("ix_proposal_artifacts_proposal_run_id")
    op.drop_table("proposal_artifacts")
    op.drop_index("ix_proposal_runs_inputs_hash")
    op.drop_index("ix_proposal_runs_as_of")
    op.drop_index("ix_proposal_runs_user_id")
    op.drop_index("ix_proposal_runs_portfolio_id")
    op.drop_table("proposal_runs")
    op.drop_index("ix_audit_events_entity_id")
    op.drop_index("ix_audit_events_entity_type")
    op.drop_index("ix_audit_events_action")
    op.drop_index("ix_audit_events_user_id")
    op.drop_table("audit_events")
    op.drop_constraint("uq_fact_key", "filing_facts")
    op.drop_index("ix_filing_facts_cik")
    op.drop_table("filing_facts")
    op.drop_constraint("uq_series_source_code_ts", "series_observations")
    op.drop_index("ix_series_observations_ts")
    op.drop_index("ix_series_observations_series_code")
    op.drop_index("ix_series_observations_source")
    op.drop_table("series_observations")
    op.drop_constraint("uq_symbols_ticker", "symbols")
    op.drop_index("ix_symbols_cik")
    op.drop_index("ix_symbols_ticker")
    op.drop_table("symbols")
