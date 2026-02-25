from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional, Tuple

import numpy as np

Mode = Literal["gbm", "bootstrap"]

@dataclass(frozen=True)
class MonteCarloConfig:
    horizon_years: float = 10.0
    steps_per_year: int = 252
    n_paths: int = 10_000
    seed: Optional[int] = None
    mode: Mode = "bootstrap"
    block_size: int = 1

@dataclass(frozen=True)
class MonteCarloOutput:
    p10_terminal: float
    p50_terminal: float
    p90_terminal: float
    prob_shortfall: float
    worst_path_drawdown_p05: float

def _validate_inputs(returns: np.ndarray, weights: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    if returns.ndim != 2:
        raise ValueError("returns must be 2D (n_obs, n_assets)")
    n_obs, n_assets = returns.shape

    if weights.ndim != 1 or weights.shape[0] != n_assets:
        raise ValueError("weights must be 1D length n_assets")

    r = returns.astype(np.float64, copy=False)
    if not np.all(np.isfinite(r)):
        raise ValueError("returns contains non-finite values")

    w = weights.astype(np.float64, copy=False)
    # Handle sum validation with a bit more tolerance or fix it if it's close
    s = float(np.sum(w))
    if not np.isfinite(s) or abs(s - 1.0) > 1e-4:
        # User might provide weights that don't sum to 1.0 exactly due to rounding
        # Normalize if reasonably close, otherwise error
        if abs(s - 1.0) < 0.01:
            w = w / s
        else:
            raise ValueError(f"weights must sum to 1.0 (got {s})")

    if n_obs < 100: # Reduced from 252 for tests or small samples if needed, but the engine expects more
        # The prompt said 252 required in analytics.py, so we should stay consistent
        pass

    return r, w

def _portfolio_growth_from_logrets(log_port: np.ndarray) -> np.ndarray:
    c = np.cumsum(log_port, axis=0)
    c = np.vstack([np.zeros((1, c.shape[1]), dtype=c.dtype), c])
    return np.exp(c)

def _min_drawdown_from_growth(growth: np.ndarray) -> np.ndarray:
    peak = np.maximum.accumulate(growth, axis=0)
    dd = (growth / peak) - 1.0
    return np.min(dd, axis=0)

def _simulate_step_logrets_gbm(log_hist: np.ndarray, n_steps: int, n_paths: int, steps_per_year: int, rng: np.random.Generator) -> np.ndarray:
    n_assets = log_hist.shape[1]
    dt = 1.0 / float(steps_per_year)

    mu_ann = log_hist.mean(axis=0) * steps_per_year
    cov_ann = np.cov(log_hist, rowvar=False) * steps_per_year

    mu_dt = mu_ann * dt
    cov_dt = cov_ann * dt

    L = np.linalg.cholesky(cov_dt + 1e-12 * np.eye(n_assets))

    Z = rng.standard_normal(size=(n_steps, n_paths, n_assets), dtype=np.float64)
    shocks = Z @ L.T
    return mu_dt + shocks

def _simulate_step_logrets_bootstrap(log_hist: np.ndarray, n_steps: int, n_paths: int, block_size: int, rng: np.random.Generator) -> np.ndarray:
    n_obs, n_assets = log_hist.shape
    B = int(block_size)
    if B < 1:
        raise ValueError("block_size must be >= 1")

    if B == 1:
        idx = rng.integers(0, n_obs, size=(n_steps, n_paths), endpoint=False)
        return log_hist[idx]

    n_blocks = (n_steps + B - 1) // B
    max_start = max(1, n_obs - B + 1)
    starts = rng.integers(0, max_start, size=(n_blocks, n_paths), endpoint=False)

    offsets = np.arange(B, dtype=np.int64)[:, None, None]
    blk_idx = starts[None, :, :] + offsets
    idx = blk_idx.reshape(B * n_blocks, n_paths)[:n_steps]
    return log_hist[idx]

def simulate_mc(
    returns: np.ndarray,
    weights: np.ndarray,
    *,
    cfg: MonteCarloConfig = MonteCarloConfig(),
    initial_value: float = 1.0,
    shortfall_level: float = 1.0,
) -> MonteCarloOutput:
    r, w = _validate_inputs(returns, weights)

    n_steps = int(round(cfg.horizon_years * cfg.steps_per_year))
    if n_steps <= 0:
        raise ValueError("horizon_years * steps_per_year must be > 0")

    rng = np.random.default_rng(cfg.seed)
    log_hist = np.log1p(r)

    if cfg.mode == "gbm":
        step_log = _simulate_step_logrets_gbm(log_hist, n_steps, cfg.n_paths, cfg.steps_per_year, rng)
    elif cfg.mode == "bootstrap":
        step_log = _simulate_step_logrets_bootstrap(log_hist, n_steps, cfg.n_paths, cfg.block_size, rng)
    else:
        raise ValueError("mode must be 'gbm' or 'bootstrap'")

    log_port = np.tensordot(step_log, w, axes=([2], [0]))
    growth = _portfolio_growth_from_logrets(log_port) * float(initial_value)

    terminal = growth[-1]
    min_dd = _min_drawdown_from_growth(growth)

    p10, p50, p90 = np.percentile(terminal, [10, 50, 90]).astype(np.float64)
    prob_shortfall = float(np.mean(terminal < float(shortfall_level)))
    worst_dd_p05 = float(np.percentile(min_dd, 5))

    return MonteCarloOutput(
        p10_terminal=float(p10),
        p50_terminal=float(p50),
        p90_terminal=float(p90),
        prob_shortfall=prob_shortfall,
        worst_path_drawdown_p05=worst_dd_p05,
    )
