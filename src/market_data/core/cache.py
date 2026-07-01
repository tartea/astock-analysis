"""Tiered SQLite cache for data source calls.

TTL is differentiated by data volatility:
- TTL_REALTIME   (60s)      — price snapshot
- TTL_INTRADAY   (5 min)    — intraday kline, fund flow
- TTL_HOURLY     (1 hour)   — news
- TTL_DAILY      (2 hours)  — LHB, northbound, margin
- TTL_QUARTERLY  (24 hours) — financials, research reports
- TTL_STATIC     (7 days)   — industry classification, stock metadata

Set env STOCK_NO_CACHE=1 to bypass cache entirely (force refresh).
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable

import pandas as pd

# ── Tiered TTL constants (seconds) ──────────────────────────────
TTL_REALTIME = 60
TTL_INTRADAY = 5 * 60
TTL_HOURLY = 60 * 60
TTL_DAILY = 2 * 60 * 60
TTL_QUARTERLY = 24 * 60 * 60
TTL_STATIC = 7 * 24 * 60 * 60

CACHE_TTL_SECONDS = TTL_INTRADAY  # default

NO_CACHE = os.environ.get("STOCK_NO_CACHE") == "1"

# Cache DB location — can be overridden via env
CACHE_DB_PATH = os.environ.get(
    "STOCK_CACHE_DB",
    str(Path.home() / ".market_data" / "cache.db"),
)

_lock = threading.Lock()


def _ensure_db() -> None:
    """Create cache table if it doesn't exist."""
    Path(CACHE_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with _get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cache (
                cache_key   TEXT PRIMARY KEY,
                data        TEXT NOT NULL,
                cached_at   REAL NOT NULL,
                ttl         INTEGER NOT NULL,
                ticker      TEXT NOT NULL,
                key_name    TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_cache_ticker ON cache(ticker)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_cache_expiry ON cache(cached_at, ttl)"
        )


@contextmanager
def _get_conn():
    """Get a thread-local SQLite connection."""
    conn = sqlite3.connect(CACHE_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _make_cache_key(ticker: str, key: str) -> str:
    """Build a deterministic cache key from ticker + descriptive key."""
    raw = f"{ticker}::{key}"
    h = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return h


def _serialize(obj: Any) -> str:
    """Serialize a value to a JSON string, handling DataFrames in tuples."""
    return json.dumps(obj, ensure_ascii=False, default=_json_default)


def _json_default(obj: Any) -> Any:
    """JSON default handler for non-serializable types."""
    if isinstance(obj, pd.DataFrame):
        return {"__pd_dataframe__": obj.to_json(orient="table", date_format="iso")}
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _deserialize(data_str: str) -> Any:
    """Deserialize a JSON string, reconstructing DataFrames."""
    return json.loads(data_str, object_hook=_json_object_hook)


def _json_object_hook(dct: dict) -> Any:
    """JSON object hook to reconstruct DataFrames."""
    if "__pd_dataframe__" in dct:
        return pd.read_json(io.StringIO(dct["__pd_dataframe__"]), orient="table")
    return dct


def cached(
    ticker: str,
    key: str,
    fetch_fn: Callable[[], Any],
    ttl: int = CACHE_TTL_SECONDS,
) -> Any:
    """Return cached value if fresh, else call fetch_fn and store.

    Args:
        ticker: Stock code (e.g. '600519')
        key: Descriptive cache key (e.g. 'kline_daily_2024-01-01_2024-06-01')
        fetch_fn: Callable that returns the data to cache
        ttl: Time-to-live in seconds (use TTL_* constants)

    Returns:
        The cached or freshly fetched data.

    Set STOCK_NO_CACHE=1 in the environment to force refresh.
    """
    if NO_CACHE:
        return fetch_fn()

    with _lock:
        _ensure_db()
        cache_key = _make_cache_key(ticker, key)

        with _get_conn() as conn:
            row = conn.execute(
                "SELECT data, cached_at, ttl FROM cache WHERE cache_key = ?",
                (cache_key,),
            ).fetchone()

        if row is not None:
            if time.time() - row["cached_at"] < row["ttl"]:
                try:
                    return _deserialize(row["data"])
                except (json.JSONDecodeError, TypeError, ValueError):
                    pass

        # Cache miss or expired — fetch fresh data
        data = fetch_fn()
        now = time.time()

        with _get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO cache (cache_key, data, cached_at, ttl, ticker, key_name)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (cache_key, _serialize(data), now, ttl, ticker, key),
            )

        return data


def clear_cache(ticker: str | None = None) -> int:
    """Clear cache entries, optionally filtered by ticker. Returns count of deleted rows."""
    with _lock:
        _ensure_db()
        with _get_conn() as conn:
            if ticker:
                cursor = conn.execute("DELETE FROM cache WHERE ticker = ?", (ticker,))
            else:
                cursor = conn.execute("DELETE FROM cache")
            return cursor.rowcount


def cache_stats() -> dict:
    """Return cache statistics for monitoring."""
    with _lock:
        _ensure_db()
        with _get_conn() as conn:
            total = conn.execute("SELECT COUNT(*) as n FROM cache").fetchone()["n"]
            now = time.time()
            fresh = conn.execute(
                "SELECT COUNT(*) as n FROM cache WHERE cached_at + ttl >= ?", (now,)
            ).fetchone()["n"]
            return {
                "total_entries": total,
                "fresh_entries": fresh,
                "stale_entries": total - fresh,
                "db_path": CACHE_DB_PATH,
            }
