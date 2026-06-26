"""Type definitions for margin trading dimension responses."""

from __future__ import annotations

from typing import TypedDict


class MarginResponse(TypedDict):
    """Margin trading (融资融券) response."""

    data: list[dict]
    provider: str
    code: str
