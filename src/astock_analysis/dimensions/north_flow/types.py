"""Type definitions for northbound flow dimension responses."""

from __future__ import annotations

from typing import TypedDict


class NorthFlowResponse(TypedDict):
    """Northbound (北向资金) capital flow response."""

    data: list[dict]
    provider: str
    code: str
