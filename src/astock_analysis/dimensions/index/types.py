"""Type definitions for index dimension responses."""

from __future__ import annotations

from typing import TypedDict


class IndexRecord(TypedDict):
    """A single index daily bar."""

    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float


class IndexResponse(TypedDict):
    """Index daily K-line response."""

    records: list[IndexRecord]
    provider: str
    code: str
    start_date: str
    end_date: str
