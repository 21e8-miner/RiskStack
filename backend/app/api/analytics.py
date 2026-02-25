from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd
import numpy as np

from ..deps import get_db
from ..models import Portfolio, Client, PriceBar
from ..schemas import RiskResult, MCResult, DataSnapshot
from ..marketdata.prices import load_prices
from ..risk.engine import _to_returns, portfolio_returns, risk_signature, risk_score_from_signature
from ..risk.monte_carlo import simulate_mc, MonteCarloConfig
from ._security import current_user
from ._cache import cache_key, cache_get, cache_set

router = APIRouter()

def _get_portfolio_owned(db: Session, u, portfolio_id: int) -> Portfolio:
    return (
        db.query(Portfolio)
        .join(Client, Client.id == Portfolio.client_id)
        .filter(Portfolio.id == portfolio_id, Client.owner_user_id == u.id)
        .one()
    )

def _to_utc(dt):
    if dt is None:
        return None
    return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

@router.get("/analytics/{portfolio_id}/risk", response_model=RiskResult)
def get_risk(portfolio_id: int, db: Session = Depends(get_db), u=Depends(current_user)):
    p = _get_portfolio_owned(db, u, portfolio_id)
    weights = {x.ticker.upper(): x.weight for x in p.positions if x.kind != "cash" and x.weight > 0}
    if not weights:
        raise HTTPException(status_code=400, detail="Portfolio has no asset allocations.")

    tickers = sorted(weights.keys())
    rounded_weights = {t: round(weights[t], 4) for t in tickers}

    wm = db.query(func.max(PriceBar.updated_at)).filter(PriceBar.ticker.in_(tickers)).scalar()
    wm_str = wm.isoformat() if wm else "none"

    c_key = cache_key("risk", {
        "portfolio_id": p.id,
        "tickers": tickers,
        "weights": rounded_weights,
        "wm": wm_str,
    })
    cached = cache_get(c_key)
    if cached:
        return cached

    px = load_prices(db, tickers)
    missing_tickers = [t for t in tickers if t not in px.columns]
    if missing_tickers:
        raise HTTPException(status_code=422, detail={"error": "missing_price_history", "tickers": missing_tickers})

    required_days = 252
    counts = px[tickers].notna().sum(axis=0)
    for t, valid_days in counts.items():
        if int(valid_days) < required_days:
            raise HTTPException(
                status_code=422,
                detail={"error": "insufficient_history", "ticker": t, "days_available": int(valid_days), "required": required_days}
            )

    rets = _to_returns(px)
    if len(rets) < required_days:
        raise HTTPException(
            status_code=422,
            detail={"error": "insufficient_overlap", "overlap_days": len(rets), "required": required_days}
        )

    port_r = portfolio_returns(rets, weights)
    sig = risk_signature(port_r)
    score, comps = risk_score_from_signature(sig)

    snapshot = DataSnapshot(
        as_of=datetime.now(timezone.utc),
        price_source="internal_db_price_bars",
        price_range_start=_to_utc(px.index.min().to_pydatetime() if not px.empty else None),
        price_range_end=_to_utc(px.index.max().to_pydatetime() if not px.empty else None),
        trading_days_analyzed=len(rets)
    )

    result = RiskResult(
        risk_score=score,
        components=comps,
        max_drawdown=sig["max_drawdown"],
        vol_annual=sig["vol_annual"],
        downside_vol_annual=sig["downside_vol_annual"],
        skew=sig["skew"],
        kurtosis_excess=sig["kurtosis_excess"],
        snapshot=snapshot
    )

    cache_set(c_key, result.model_dump(mode="json"), ttl_s=300)
    return result

@router.get("/analytics/{portfolio_id}/montecarlo", response_model=MCResult)
def get_montecarlo(
    portfolio_id: int,
    horizon_years: float = Query(10.0, gt=0, le=50),
    n_paths: int = Query(10000, gt=100, le=200000),
    mode: str = Query("bootstrap", pattern="^(bootstrap|gbm)$"),
    block_size: int = Query(1, ge=1, le=60),
    db: Session = Depends(get_db),
    u=Depends(current_user),
):
    p = _get_portfolio_owned(db, u, portfolio_id)
    weights = {x.ticker.upper(): x.weight for x in p.positions if x.kind != "cash" and x.weight > 0}
    if not weights:
        raise HTTPException(status_code=400, detail="Portfolio has no asset allocations.")

    tickers = sorted(weights.keys())
    rounded_weights = {t: round(weights[t], 4) for t in tickers}

    wm = db.query(func.max(PriceBar.updated_at)).filter(PriceBar.ticker.in_(tickers)).scalar()
    wm_str = wm.isoformat() if wm else "none"

    c_key = cache_key("mc", {
        "portfolio_id": p.id,
        "tickers": tickers,
        "weights": rounded_weights,
        "wm": wm_str,
        "horizon_years": round(horizon_years, 6),
        "n_paths": n_paths,
        "mode": mode,
        "block_size": block_size,
    })
    cached = cache_get(c_key)
    if cached:
        return cached

    px = load_prices(db, tickers)
    missing_tickers = [t for t in tickers if t not in px.columns]
    if missing_tickers:
        raise HTTPException(status_code=422, detail={"error": "missing_price_history", "tickers": missing_tickers})

    rets = px.pct_change().dropna()
    if len(rets) < 252:
        raise HTTPException(status_code=422, detail={"error": "insufficient_overlap", "overlap_days": len(rets), "required": 252})

    R = rets[tickers].to_numpy(dtype=np.float64, copy=False)
    w = np.array([weights[t] for t in tickers], dtype=np.float64)

    cfg = MonteCarloConfig(
        horizon_years=horizon_years,
        n_paths=n_paths,
        mode=mode,
        block_size=block_size,
    )
    out = simulate_mc(R, w, cfg=cfg, initial_value=1.0, shortfall_level=1.0)

    snapshot = DataSnapshot(
        as_of=datetime.now(timezone.utc),
        price_source="internal_db_price_bars",
        price_range_start=_to_utc(px.index.min().to_pydatetime() if not px.empty else None),
        price_range_end=_to_utc(px.index.max().to_pydatetime() if not px.empty else None),
        trading_days_analyzed=len(rets)
    )

    result = MCResult(
        horizon_years=horizon_years,
        n_paths=n_paths,
        p10_terminal=out.p10_terminal,
        p50_terminal=out.p50_terminal,
        p90_terminal=out.p90_terminal,
        prob_shortfall=out.prob_shortfall,
        worst_path_drawdown_p05=out.worst_path_drawdown_p05,
        snapshot=snapshot,
    )

    cache_set(c_key, result.model_dump(mode="json"), ttl_s=300)
    return result
