"""Type definitions for stock info dimension responses."""

from __future__ import annotations

from typing import TypedDict


class StockInfoResponse(TypedDict):
    """Basic stock metadata response."""

    code: str
    name: str
    full_name: str
    industry: str
    list_date: str
    total_shares: float | None
    circ_shares: float | None
    province: str
    total_market_cap: float | None
    circ_market_cap: float | None
    pe: float | None
    pb: float | None
    eps: float | None
    bvps: float | None
    price: float | None
    turnover: float | None
    pct_chg: float | None
    provider: str
