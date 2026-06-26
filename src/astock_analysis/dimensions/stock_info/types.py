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
    provider: str
