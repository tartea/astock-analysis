"""Type definitions for shareholder holder dimension responses."""

from __future__ import annotations

from typing import TypedDict


class HolderRecord(TypedDict):
    """A single holder structure record."""

    date: str
    holder_count: float | None
    avg_shares: float | None
    avg_value: float | None


class HolderResponse(TypedDict):
    """Shareholder structure response."""

    records: list[HolderRecord]
    provider: str
    code: str
