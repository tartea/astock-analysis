"""News dimension router.

Provides a unified interface for fetching stock-related news.

Usage:
    from astock_analysis.dimensions.news import fetch_news

    response = fetch_news("600519")
    print(f"Articles: {len(response['data'])}, Provider: {response['provider']}")
"""

from __future__ import annotations

import pandas as pd

from astock_analysis.core.chain import try_chain, register_provider, ProviderError
from astock_analysis.core.config import get_config
from astock_analysis.core.cache import TTL_HOURLY
from astock_analysis.providers.akshare import provider as akshare_provider

from .types import NewsResponse

register_provider("akshare", akshare_provider)


def fetch_news(code: str, use_cache: bool = True) -> NewsResponse:
    """Fetch stock-related news.

    Args:
        code: A-share stock code (e.g. '600519')
        use_cache: Whether to use the cache layer (default True)

    Returns:
        NewsResponse with data list and metadata.
    """
    config = get_config()
    cache_ttl = TTL_HOURLY if use_cache else None

    df, provider_name = try_chain(
        method_name="fetch_news",
        dimension="news",
        code=code,
        ticker=code,
        cache_ttl=cache_ttl,
        config=config,
    )

    if not isinstance(df, pd.DataFrame):
        raise ProviderError(
            f"Provider '{provider_name}' returned {type(df).__name__} instead of DataFrame"
        )

    records = df.to_dict(orient="records")
    return NewsResponse(
        data=[{k: (None if pd.isna(v) else v) for k, v in r.items()} for r in records],
        provider=provider_name,
        code=code,
    )
