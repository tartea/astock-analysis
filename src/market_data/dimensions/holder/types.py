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


class TopHolderRecord(TypedDict):
    """A single major shareholder record (top 10 / free top 10)."""

    rank: int
    holder_name: str
    holder_nature: str | None
    share_type: str
    share_num: float | None
    share_ratio: float | None
    share_change: str
    change_ratio: float | None
    report_date: str


class TopHolderResponse(TypedDict):
    """Major shareholders response (十大股东 / 十大流通股东)."""

    records: list[TopHolderRecord]
    provider: str
    code: str
    date: str
    holder_type: str  # "top10" | "free_top10"
