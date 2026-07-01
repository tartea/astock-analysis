"""Type definitions for block trade dimension responses."""

from __future__ import annotations

from typing import TypedDict


class BlockTradeResponse(TypedDict):
    """Block trade (大宗交易) response."""

    data: list[dict]
    provider: str
    code: str
