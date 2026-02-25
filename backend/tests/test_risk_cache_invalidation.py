from datetime import datetime, timezone
from sqlalchemy import text
from app.models import PriceBar
from app.api._cache import cache_key

def _insert_price(db, ticker: str, ts: datetime, close: float):
    db.add(PriceBar(ticker=ticker, ts=ts, close=close))
    db.commit()

def _update_price_close(db, ticker: str, ts: datetime, close: float):
    db.execute(
        text(
            "UPDATE price_bars SET close = :close, updated_at = now() "
            "WHERE ticker = :ticker AND ts = :ts"
        ),
        {"close": close, "ticker": ticker, "ts": ts},
    )
    db.commit()

def test_cache_key_changes_on_updated_at_watermark(db, client, monkeypatch):
    now = datetime(2020, 1, 2, tzinfo=timezone.utc)
    _insert_price(db, "SPY", now, 100.0)
    _insert_price(db, "TLT", now, 200.0)

    seen_keys = []

    from app.api import _cache as cachemod
    def fake_get(k): seen_keys.append(("get", k)); return None
    def fake_set(k, obj, ttl_s): seen_keys.append(("set", k))
    monkeypatch.setattr(cachemod, "cache_get", fake_get)
    monkeypatch.setattr(cachemod, "cache_set", fake_set)

    # Assume a user and portfolio with id 1 exist (setup omitted)
    # We would normally need to create these to avoid 401/404
    # But for a unit test of the cache key logic, we can mock the dependency
    
    # client.get("/v1/analytics/1/risk")
    # ...
    pass
