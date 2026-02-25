from sqlalchemy.orm import Session
from ..db import SessionLocal
from ..settings import settings
from ..marketdata.sources import SECProvider, FREDProvider, StooqProvider
from ..marketdata.ingest import (
    upsert_sec_company_tickers_exchange,
    parse_fred_observations, upsert_series,
    parse_stooq_daily_csv, upsert_prices,
    upsert_sec_companyfacts,
)
from .celery_app import celery

@celery.task(name="app.tasks.jobs.refresh_sec_tickers_exchange")
def refresh_sec_tickers_exchange():
    prov = SECProvider(user_agent=settings.sec_user_agent)

    async def _run():
        return await prov.fetch_company_tickers_exchange()

    import asyncio
    res = asyncio.run(_run())

    db: Session = SessionLocal()
    try:
        upsert_sec_company_tickers_exchange(db, res.payload)
        return {"ok": True}
    finally:
        db.close()

@celery.task(name="app.tasks.jobs.refresh_fred_series")
def refresh_fred_series(series_id: str):
    if not settings.fred_api_key:
        return {"ok": False, "error": "FRED_API_KEY missing"}

    prov = FREDProvider(api_key=settings.fred_api_key)

    async def _run():
        return await prov.fetch_series(series_id)

    import asyncio
    res = asyncio.run(_run())
    rows = parse_fred_observations(res.payload)

    db: Session = SessionLocal()
    try:
        upsert_series(db, "fred", series_id, rows, {"fetched_at": res.fetched_at.isoformat()})
        return {"ok": True, "n": len(rows)}
    finally:
        db.close()

@celery.task(name="app.tasks.jobs.refresh_prices_stooq")
def refresh_prices_stooq(ticker: str, stooq_symbol: str | None = None):
    prov = StooqProvider()
    sym = stooq_symbol or ticker

    async def _run():
        return await prov.fetch_daily_csv(sym)

    import asyncio
    res = asyncio.run(_run())
    rows = parse_stooq_daily_csv(res.payload["csv"])

    db: Session = SessionLocal()
    try:
        upsert_prices(db, ticker.upper(), rows)
        return {"ok": True, "n": len(rows)}
    finally:
        db.close()

@celery.task(name="app.tasks.jobs.refresh_sec_companyfacts")
def refresh_sec_companyfacts(cik10: str):
    prov = SECProvider(user_agent=settings.sec_user_agent)

    async def _run():
        return await prov.fetch_companyfacts(cik10)

    import asyncio
    res = asyncio.run(_run())

    db: Session = SessionLocal()
    try:
        upsert_sec_companyfacts(db, cik10, res.payload)
        return {"ok": True}
    finally:
        db.close()
