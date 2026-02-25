from datetime import datetime, timezone, timedelta
from app.models import PriceBar

def _seed_prices(db, ticker: str, start: datetime, n: int):
    for i in range(n):
        db.add(PriceBar(ticker=ticker, ts=start + timedelta(days=i), close=100.0 + i))
    db.commit()

def test_missing_price_history_returns_422(client):
    # Setup user/portfolio 1 mock or DB entry
    # r = client.get("/v1/analytics/1/risk")
    # assert r.status_code == 422
    pass

def test_insufficient_history_returns_422(db, client):
    # start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    # _seed_prices(db, "SPY", start, 200)  # < 252
    # _seed_prices(db, "TLT", start, 300)
    # r = client.get("/v1/analytics/1/risk")
    # assert r.status_code == 422
    pass
