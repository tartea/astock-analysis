"""Type definitions for news dimension responses."""

from __future__ import annotations

from typing import TypedDict


class NewsResponse(TypedDict):
    """Stock news response."""

    data: list[dict]
    provider: str
    code: str
