"""Type definitions for Dragon-Tiger Board (lhb) dimension responses."""

from __future__ import annotations

from typing import TypedDict


class LHBResponse(TypedDict):
    """Dragon-Tiger Board (龙虎榜) response."""

    data: list[dict]
    provider: str
    code: str
