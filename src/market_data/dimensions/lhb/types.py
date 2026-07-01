"""Type definitions for Dragon-Tiger Board (lhb) dimension responses."""

from __future__ import annotations

from typing import TypedDict


class LHBResponse(TypedDict):
    """Dragon-Tiger Board (龙虎榜) response."""

    data: list[dict]
    provider: str
    code: str


class LHBDetailRecord(TypedDict):
    """Single trading desk LHB detail."""

    desk_name: str
    buy_amount: float | None
    buy_pct: float | None
    sell_amount: float | None
    sell_pct: float | None
    net_amount: float | None


class LHBDetailResponse(TypedDict):
    """Per-trading-desk LHB detail response."""

    desks: list[LHBDetailRecord]
    provider: str
    code: str
    date: str
