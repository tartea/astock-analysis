"""Type definitions for realtime quote dimension responses."""

from __future__ import annotations

from typing import TypedDict


class RealtimeResponse(TypedDict):
    """Real-time quote snapshot for a single A-share stock."""

    code: str
    name: str
    price: float
    open: float
    high: float
    low: float
    volume: float
    amount: float
    change: float
    pct_chg: float
    turnover: float
    pe: float | None
    pb: float | None
    total_mv: float | None
    circ_mv: float | None
    provider: str
