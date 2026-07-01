"""Type definitions for fund dimension responses."""

from __future__ import annotations

from typing import TypedDict


class FundResponse(TypedDict):
    """ETF/Fund data response."""

    data: list[dict]
    provider: str
    code: str
