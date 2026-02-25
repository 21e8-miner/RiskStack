from __future__ import annotations

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..models import PriceBar

def load_prices(db: Session, tickers: list[str]) -> pd.DataFrame:
    tickers = [t.upper() for t in tickers]
    stmt = (
        select(PriceBar.ticker, PriceBar.ts, PriceBar.close)
        .where(PriceBar.ticker.in_(tickers))
        .order_by(PriceBar.ts.asc())
    )
    rows = db.execute(stmt).all()
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows, columns=["ticker", "ts", "close"])
    df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce")
    df = df.dropna(subset=["ts"])
    px = df.pivot(index="ts", columns="ticker", values="close").sort_index()
    return px
