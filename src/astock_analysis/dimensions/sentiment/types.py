"""Type definitions for sentiment dimension responses."""

from __future__ import annotations

from typing import TypedDict


class SentimentResponse(TypedDict):
    """Market sentiment summary."""

    total: int
    rise_count: int
    fall_count: int
    flat_count: int
    limit_up_count: int
    limit_down_count: int
    market_sentiment: str
    provider: str
