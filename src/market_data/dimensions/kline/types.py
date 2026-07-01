"""Type definitions for kline dimension responses."""

from __future__ import annotations

from typing import TypedDict


class KlineRecord(TypedDict):
    """A single K-line bar."""

    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float
    pct_chg: float | None


class KlineResponse(TypedDict):
    """Complete K-line response from the kline dimension.

    Contains the raw DataFrame (as records) plus metadata about which
    provider served the data.
    """

    records: list[KlineRecord]
    provider: str
    code: str
    start_date: str
    end_date: str
