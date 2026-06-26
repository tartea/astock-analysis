"""Realtime quote dimension router.

Provides a unified interface for fetching real-time stock quotes
regardless of which underlying provider serves them.

Usage:
    from astock_analysis.dimensions.realtime import fetch_realtime

    response = fetch_realtime("600519")
    print(f"Price: {response['price']}, Provider: {response['provider']}")
"""

from __future__ import annotations

from astock_analysis.core.chain import try_chain, register_provider
from astock_analysis.core.config import get_config
from astock_analysis.core.cache import TTL_REALTIME
from astock_analysis.providers.akshare import provider as akshare_provider

from .types import RealtimeResponse

register_provider("akshare", akshare_provider)


def fetch_realtime(code: str, use_cache: bool = True) -> RealtimeResponse:
    """Fetch real-time quote for an A-share stock.

    Args:
        code: A-share stock code (e.g. '600519')
        use_cache: Whether to use the cache layer (default True)

    Returns:
        RealtimeResponse with quote fields and metadata.
    """
    config = get_config()
    cache_ttl = TTL_REALTIME if use_cache else None

    data, provider_name = try_chain(
        method_name="fetch_realtime",
        dimension="realtime",
        code=code,
        ticker=code,
        cache_ttl=cache_ttl,
        config=config,
    )

    data["provider"] = provider_name
    return RealtimeResponse(**{k: data.get(k) for k in RealtimeResponse.__annotations__ if k in data})
