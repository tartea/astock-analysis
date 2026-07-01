"""Stock info dimension router.

Provides a unified interface for fetching basic stock metadata.

Usage:
    from market_data.dimensions.stock_info import fetch_stock_info

    response = fetch_stock_info("600519")
    print(f"Name: {response['name']}, Industry: {response['industry']}")
"""

from __future__ import annotations

from market_data.core.chain import try_chain, register_provider
from market_data.core.config import get_config
from market_data.core.cache import TTL_STATIC
from market_data.providers.akshare import provider as akshare_provider

from .types import StockInfoResponse

register_provider("akshare", akshare_provider)


def fetch_stock_info(code: str, use_cache: bool = True) -> StockInfoResponse:
    """Fetch basic stock metadata.

    Args:
        code: A-share stock code (e.g. '600519')
        use_cache: Whether to use the cache layer (default True)

    Returns:
        StockInfoResponse with metadata fields.
    """
    config = get_config()
    cache_ttl = TTL_STATIC if use_cache else None

    data, provider_name = try_chain(
        method_name="fetch_stock_info",
        dimension="stock_info",
        code=code,
        ticker=code,
        cache_ttl=cache_ttl,
        config=config,
    )

    data["provider"] = provider_name
    return StockInfoResponse(**{k: data.get(k) for k in StockInfoResponse.__annotations__ if k in data})
