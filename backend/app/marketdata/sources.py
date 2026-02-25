from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import httpx

@dataclass(frozen=True)
class FetchResult:
    payload: dict
    fetched_at: datetime

class FREDProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def fetch_series(self, series_id: str) -> FetchResult:
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {"api_key": self.api_key, "series_id": series_id, "file_type": "json"}
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(url, params=params)
            r.raise_for_status()
            return FetchResult(payload=r.json(), fetched_at=datetime.utcnow())

class SECProvider:
    def __init__(self, user_agent: str):
        self.user_agent = user_agent

    async def fetch_company_tickers_exchange(self) -> FetchResult:
        url = "https://www.sec.gov/files/company_tickers_exchange.json"
        headers = {"User-Agent": self.user_agent, "Accept-Encoding": "gzip, deflate"}
        async with httpx.AsyncClient(timeout=60, headers=headers) as c:
            r = await c.get(url)
            r.raise_for_status()
            return FetchResult(payload=r.json(), fetched_at=datetime.utcnow())

    async def fetch_companyfacts(self, cik10: str) -> FetchResult:
        cik = cik10.zfill(10)
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        headers = {"User-Agent": self.user_agent, "Accept-Encoding": "gzip, deflate"}
        async with httpx.AsyncClient(timeout=60, headers=headers) as c:
            r = await c.get(url)
            r.raise_for_status()
            return FetchResult(payload=r.json(), fetched_at=datetime.utcnow())

class StooqProvider:
    async def fetch_daily_csv(self, symbol: str) -> FetchResult:
        url = "https://stooq.com/q/d/l/"
        params = {"s": symbol.lower(), "i": "d"}
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(url, params=params)
            r.raise_for_status()
            return FetchResult(payload={"csv": r.text}, fetched_at=datetime.utcnow())
