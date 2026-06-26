"""Type definitions for capital flow dimension responses."""

from __future__ import annotations

from typing import TypedDict


class CapitalFlowRecord(TypedDict):
    """A single capital flow record."""

    date: str
    main_net_inflow: float | None
    main_net_pct: float | None
    super_large_net: float | None
    super_large_pct: float | None
    large_net: float | None
    large_pct: float | None
    medium_net: float | None
    medium_pct: float | None
    small_net: float | None
    small_pct: float | None


class CapitalFlowResponse(TypedDict):
    """Complete capital flow response."""

    records: list[CapitalFlowRecord]
    provider: str
    code: str
