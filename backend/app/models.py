from __future__ import annotations

from datetime import datetime
from sqlalchemy import (
    String, Integer, Float, ForeignKey, DateTime, UniqueConstraint, LargeBinary, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .db import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Client(Base):
    __tablename__ = "clients"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    portfolios: Mapped[list["Portfolio"]] = relationship(back_populates="client")

class Portfolio(Base):
    __tablename__ = "portfolios"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    base_ccy: Mapped[str] = mapped_column(String(8), default="USD")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    client: Mapped["Client"] = relationship(back_populates="portfolios")
    positions: Mapped[list["Position"]] = relationship(back_populates="portfolio", cascade="all, delete-orphan")

class Position(Base):
    __tablename__ = "positions"
    __table_args__ = (UniqueConstraint("portfolio_id", "ticker", name="uq_position_portfolio_ticker"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), index=True)
    ticker: Mapped[str] = mapped_column(String(24), index=True)
    weight: Mapped[float] = mapped_column(Float)
    kind: Mapped[str] = mapped_column(String(16), default="asset")  # asset|cash
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    portfolio: Mapped["Portfolio"] = relationship(back_populates="positions")

class PriceBar(Base):
    __tablename__ = "price_bars"
    __table_args__ = (UniqueConstraint("ticker", "ts", name="uq_price_ticker_ts"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(24), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    close: Mapped[float] = mapped_column(Float)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True,
    )

class Symbol(Base):
    __tablename__ = "symbols"
    __table_args__ = (UniqueConstraint("ticker", name="uq_symbols_ticker"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(24), index=True)
    cik: Mapped[str] = mapped_column(String(16), index=True)
    name: Mapped[str] = mapped_column(String(300))
    exchange: Mapped[str | None] = mapped_column(String(32), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class SeriesObservation(Base):
    __tablename__ = "series_observations"
    __table_args__ = (UniqueConstraint("source", "series_code", "ts", name="uq_series_source_code_ts"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(64), index=True)
    series_code: Mapped[str] = mapped_column(String(128), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    value: Mapped[float] = mapped_column(Float)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class FilingFact(Base):
    __tablename__ = "filing_facts"
    __table_args__ = (UniqueConstraint("cik", "taxonomy", "tag", "unit", "end", "fy", "fp", name="uq_fact_key"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cik: Mapped[str] = mapped_column(String(16), index=True)
    taxonomy: Mapped[str] = mapped_column(String(32))
    tag: Mapped[str] = mapped_column(String(128))
    unit: Mapped[str] = mapped_column(String(32))
    end: Mapped[str] = mapped_column(String(16))
    fy: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fp: Mapped[str | None] = mapped_column(String(8), nullable=True)
    val: Mapped[float] = mapped_column(Float)
    accn: Mapped[str | None] = mapped_column(String(32), nullable=True)
    filed: Mapped[str | None] = mapped_column(String(16), nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    action: Mapped[str] = mapped_column(String(64), index=True)
    entity_type: Mapped[str] = mapped_column(String(64), index=True)
    entity_id: Mapped[str] = mapped_column(String(64), index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class ProposalRun(Base):
    __tablename__ = "proposal_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    inputs_hash: Mapped[str] = mapped_column(String(64), index=True)
    assumptions: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class ProposalArtifact(Base):
    __tablename__ = "proposal_artifacts"
    __table_args__ = (UniqueConstraint("proposal_run_id", name="uq_artifact_run"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    proposal_run_id: Mapped[int] = mapped_column(Integer, index=True)
    mime: Mapped[str] = mapped_column(String(64))
    filename: Mapped[str] = mapped_column(String(256))
    content: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
