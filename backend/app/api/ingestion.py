from fastapi import APIRouter, Depends
from ._security import current_user
from ..tasks.jobs import (
    refresh_sec_tickers_exchange,
    refresh_fred_series,
    refresh_prices_stooq,
    refresh_sec_companyfacts,
)

router = APIRouter()

@router.post("/ingest/sec/tickers_exchange")
def ingest_sec_tickers_exchange(u=Depends(current_user)):
    job = refresh_sec_tickers_exchange.delay()
    return {"queued": True, "task_id": job.id}

@router.post("/ingest/fred/{series_id}")
def ingest_fred(series_id: str, u=Depends(current_user)):
    job = refresh_fred_series.delay(series_id)
    return {"queued": True, "task_id": job.id}

@router.post("/ingest/prices/stooq/{ticker}")
def ingest_prices_stooq(ticker: str, stooq_symbol: str | None = None, u=Depends(current_user)):
    job = refresh_prices_stooq.delay(ticker, stooq_symbol)
    return {"queued": True, "task_id": job.id}

@router.post("/ingest/sec/companyfacts/{cik10}")
def ingest_sec_companyfacts(cik10: str, u=Depends(current_user)):
    job = refresh_sec_companyfacts.delay(cik10)
    return {"queued": True, "task_id": job.id}
