from __future__ import annotations

import numpy as np

def _to_returns(px):
    rets = np.log(px / px.shift(1)).dropna()
    return rets

def portfolio_returns(rets, weights: dict[str, float]):
    cols = list(rets.columns)
    w = np.array([weights[c] for c in cols], dtype=np.float64)
    r = rets.to_numpy(dtype=np.float64, copy=False)
    return r @ w

def risk_signature(port_r: np.ndarray) -> dict[str, float]:
    x = port_r.astype(np.float64, copy=False)
    if x.size < 2:
        raise ValueError("insufficient_returns")

    growth = np.exp(np.cumsum(x))
    peak = np.maximum.accumulate(growth)
    dd = (growth / peak) - 1.0
    max_dd = float(np.min(dd))

    vol = float(np.std(x, ddof=1) * np.sqrt(252))
    downside = x[x < 0.0]
    dvol = float(np.std(downside, ddof=1) * np.sqrt(252)) if downside.size > 1 else 0.0

    m = float(np.mean(x))
    s = float(np.std(x, ddof=1))
    if s == 0.0:
        skew = 0.0
        kurt_ex = 0.0
    else:
        z = (x - m) / s
        skew = float(np.mean(z**3))
        kurt_ex = float(np.mean(z**4) - 3.0)

    return {
        "max_drawdown": max_dd,
        "vol_annual": vol,
        "downside_vol_annual": dvol,
        "skew": skew,
        "kurtosis_excess": kurt_ex,
    }

def risk_score_from_signature(sig: dict[str, float]):
    dd = abs(sig["max_drawdown"])
    vol = sig["vol_annual"]
    dvol = sig["downside_vol_annual"]
    kurt = max(0.0, sig["kurtosis_excess"])

    score = 100.0 * (1.0 - np.exp(-(2.2*dd + 0.9*vol + 0.6*dvol + 0.08*kurt)))
    score = float(np.clip(score, 0.0, 100.0))

    comps = {
        "drawdown": float(dd),
        "vol": float(vol),
        "downside_vol": float(dvol),
        "kurtosis_excess": float(sig["kurtosis_excess"]),
    }
    return score, comps
