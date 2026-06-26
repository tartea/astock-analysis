"""Type definitions for convertible bond dimension responses."""

from __future__ import annotations

from typing import TypedDict


class BondConvertibleResponse(TypedDict):
    """Convertible bond listing response."""

    data: list[dict]
    provider: str
