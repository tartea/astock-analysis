"""Type definitions for financials dimension responses."""

from __future__ import annotations

from typing import TypedDict


class FinancialsResponse(TypedDict):
    """Financial statement data response."""

    data: list[dict]
    provider: str
    code: str
