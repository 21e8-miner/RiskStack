from __future__ import annotations

from datetime import datetime
import itertools
from typing import Iterable

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models import PriceBar, SeriesObservation, FilingFact

def _chunked_iterable(iterable: Iterable, size: int):
    it = iter(iterable)
    while True:
        chunk = list(itertools.islice(it, size))
        if not chunk:
            break
        yield chunk

def upsert_prices(db: Session, ticker: str, rows: Iterable[tuple[datetime, float]], chunk_size: int = 10000) -> int:
    ticker = ticker.upper()
    values_gen = ({"ticker": ticker, "ts": ts, "close": close} for ts, close in rows)
    total = 0
    executed = False

    for batch in _chunked_iterable(values_gen, chunk_size):
        executed = True
        stmt = insert(PriceBar).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=[PriceBar.ticker, PriceBar.ts],
            set_={
                "close": stmt.excluded.close,
                "updated_at": func.now()
            },
        )
        db.execute(stmt)
        total += len(batch)

    if executed:
        db.commit()
    return total

def upsert_series(db: Session, source: str, code: str, rows: Iterable[tuple[datetime, float]], meta: dict, chunk_size: int = 10000) -> int:
    values_gen = ({"source": source, "series_code": code, "ts": ts, "value": val, "meta": meta} for ts, val in rows)
    total = 0
    executed = False

    for batch in _chunked_iterable(values_gen, chunk_size):
        executed = True
        stmt = insert(SeriesObservation).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=[SeriesObservation.source, SeriesObservation.series_code, SeriesObservation.ts],
            set_={"value": stmt.excluded.value, "meta": stmt.excluded.meta},
        )
        db.execute(stmt)
        total += len(batch)

    if executed:
        db.commit()
    return total

def upsert_sec_companyfacts(db: Session, cik10: str, payload: dict, chunk_size: int = 2500) -> int:
    cik = cik10.zfill(10)
    facts = payload.get("facts", {})

    def _fact_generator():
        for taxonomy, tags in facts.items():
            for tag, obj in tags.items():
                units = obj.get("units", {})
                for unit, points in units.items():
                    for p in points:
                        if p.get("end") is not None and p.get("val") is not None:
                            try:
                                yield {
                                    "cik": cik,
                                    "taxonomy": taxonomy,
                                    "tag": tag,
                                    "unit": unit,
                                    "end": p["end"],
                                    "fy": p.get("fy"),
                                    "fp": p.get("fp"),
                                    "val": float(p["val"]),
                                    "accn": p.get("accn"),
                                    "filed": p.get("filed"),
                                }
                            except (TypeError, ValueError):
                                continue

    total = 0
    executed = False

    for batch in _chunked_iterable(_fact_generator(), chunk_size):
        executed = True
        stmt = insert(FilingFact).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=[
                FilingFact.cik, FilingFact.taxonomy, FilingFact.tag,
                FilingFact.unit, FilingFact.end, FilingFact.fy, FilingFact.fp
            ],
            set_={
                "val": stmt.excluded.val,
                "accn": stmt.excluded.accn,
                "filed": stmt.excluded.filed,
            }
        )
        db.execute(stmt)
        total += len(batch)

    if executed:
        db.commit()
    return total

def upsert_sec_company_tickers_exchange(db: Session, payload: dict):
    # This was missing in the provided code snippet but referenced in jobs.py
    # I'll provide a basic implementation based on the SEC schema
    from ..models import Symbol
    data = payload.get("data", [])
    # data format: [[cik, name, ticker, exchange], ...]
    batch = []
    for row in data:
        batch.append({
            "cik": str(row[0]).zfill(10),
            "name": row[1],
            "ticker": row[2].upper(),
            "exchange": row[3],
        })
    
    for b in _chunked_iterable(batch, 5000):
        stmt = insert(Symbol).values(b)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Symbol.ticker],
            set_={
                "name": stmt.excluded.name,
                "cik": stmt.excluded.cik,
                "exchange": stmt.excluded.exchange,
                "updated_at": func.now()
            }
        )
        db.execute(stmt)
    db.commit()

def parse_fred_observations(payload: dict) -> list[tuple[datetime, float]]:
    obs = payload.get("observations", [])
    rows = []
    for o in obs:
        try:
            ts = datetime.strptime(o["date"], "%Y-%m-%d")
            val = float(o["value"])
            rows.append((ts, val))
        except (ValueError, TypeError):
            continue
    return rows

def parse_stooq_daily_csv(csv_text: str) -> list[tuple[datetime, float]]:
    import io
    import csv
    f = io.StringIO(csv_text)
    reader = csv.DictReader(f)
    rows = []
    for r in reader:
        try:
            # Stooq CSV columns: Date,Open,High,Low,Close,Volume
            ts = datetime.strptime(r["Date"], "%Y-%m-%d")
            val = float(r["Close"])
            rows.append((ts, val))
        except (ValueError, KeyError, TypeError):
            continue
    return rows
