"""Type definitions for IPO dimension responses."""

from __future__ import annotations

from typing import TypedDict


class IPOResponse(TypedDict):
    """IPO/new stock listing response."""

    data: list[dict]
    provider: str
