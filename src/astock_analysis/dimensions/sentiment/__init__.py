"""Sentiment dimension router.

Provides a unified interface for fetching market sentiment indicators.

Usage:
    from astock_analysis.dimensions.sentiment import fetch_sentiment

    response = fetch_sentiment()
    print(f"Market mood: {response['market_sentiment']}")
"""

from __future__ import annotations

from astock_analysis.core.chain import try_chain, register_provider
from astock_analysis.core.config import get_config
from astock_analysis.core.cache import TTL_REALTIME
from astock_analysis.providers.akshare import provider as akshare_provider

from .types import SentimentResponse

register_provider("akshare", akshare_provider)


def fetch_sentiment(use_cache: bool = True) -> SentimentResponse:
    """Fetch market sentiment indicators (breadth, mood).

    Args:
        use_cache: Whether to use the cache layer (default True)

    Returns:
        SentimentResponse with market breadth statistics.
    """
    config = get_config()
    cache_ttl = TTL_REALTIME if use_cache else None

    data, provider_name = try_chain(
        method_name="fetch_sentiment",
        dimension="sentiment",
        ticker="market",
        cache_ttl=cache_ttl,
        config=config,
    )

    data["provider"] = provider_name
    return SentimentResponse(**{k: data.get(k) for k in SentimentResponse.__annotations__ if k in data})
