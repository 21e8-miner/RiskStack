from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field, field_validator

def _finite(x: float) -> float:
    if x != x or x in (float("inf"), float("-inf")):
        raise ValueError("non_finite_value")
    return x

class DataSnapshot(BaseModel):
    as_of: datetime
    price_source: str
    price_range_start: Optional[datetime] = None
    price_range_end: Optional[datetime] = None
    trading_days_analyzed: int = Field(..., ge=1)

class RiskResult(BaseModel):
    risk_score: float
    components: Dict[str, float]
    max_drawdown: float
    vol_annual: float
    downside_vol_annual: float
    skew: float
    kurtosis_excess: float
    snapshot: DataSnapshot

    @field_validator(
        "risk_score", "max_drawdown", "vol_annual",
        "downside_vol_annual", "skew", "kurtosis_excess"
    )
    @classmethod
    def finite_fields(cls, v: float) -> float:
        return _finite(v)

    @field_validator("components")
    @classmethod
    def finite_components(cls, v: Dict[str, float]) -> Dict[str, float]:
        return {k: _finite(float(x)) for k, x in v.items()}

class MCResult(BaseModel):
    horizon_years: float
    n_paths: int
    p10_terminal: float
    p50_terminal: float
    p90_terminal: float
    prob_shortfall: float
    worst_path_drawdown_p05: float
    snapshot: DataSnapshot

    @field_validator(
        "p10_terminal", "p50_terminal", "p90_terminal",
        "prob_shortfall", "worst_path_drawdown_p05"
    )
    @classmethod
    def finite_fields(cls, v: float) -> float:
        return _finite(v)

# Minimal CRUD schemas for UI
class ClientCreate(BaseModel):
    name: str
    email: str | None = None

class ClientOut(BaseModel):
    id: int
    name: str
    email: str | None
    class Config:
        from_attributes = True

class PositionIn(BaseModel):
    ticker: str
    weight: float = Field(ge=0, le=1)
    kind: str = "asset"

class PortfolioCreate(BaseModel):
    client_id: int
    name: str
    base_ccy: str = "USD"
    positions: list[PositionIn]

class PortfolioOut(BaseModel):
    id: int
    client_id: int
    name: str
    base_ccy: str
    positions: list[PositionIn]

class ProposalOut(BaseModel):
    proposal_run_id: int
    artifact_id: int
    filename: str
