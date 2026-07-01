"""Type definitions for futures dimension responses."""

from __future__ import annotations

from typing import TypedDict


class FuturesResponse(TypedDict):
    """Futures market data response."""

    data: list[dict]
    provider: str
    code: str
