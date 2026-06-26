"""Futures dimension router.

Provides a unified interface for fetching futures market data.

Usage:
    from astock_analysis.dimensions.futures import fetch_futures

    response = fetch_futures("IF0")
    print(f"Records: {len(response['data'])}, Provider: {response['provider']}")
"""

from __future__ import annotations

import pandas as pd

from astock_analysis.core.chain import try_chain, register_provider, ProviderError
from astock_analysis.core.config import get_config
from astock_analysis.core.cache import TTL_INTRADAY
from astock_analysis.providers.akshare import provider as akshare_provider

from .types import FuturesResponse

register_provider("akshare", akshare_provider)


def fetch_futures(code: str = "", use_cache: bool = True) -> FuturesResponse:
    """Fetch futures market data.

    Args:
        code: Optional futures contract code
        use_cache: Whether to use the cache layer (default True)

    Returns:
        FuturesResponse with data list and metadata.
    """
    config = get_config()
    cache_ttl = TTL_INTRADAY if use_cache else None

    df, provider_name = try_chain(
        method_name="fetch_futures",
        dimension="futures",
        code=code,
        ticker=code or "IF0",
        cache_ttl=cache_ttl,
        config=config,
    )

    if not isinstance(df, pd.DataFrame):
        raise ProviderError(
            f"Provider '{provider_name}' returned {type(df).__name__} instead of DataFrame"
        )

    records = df.to_dict(orient="records")
    return FuturesResponse(
        data=[{k: (None if pd.isna(v) else v) for k, v in r.items()} for r in records],
        provider=provider_name,
        code=code,
    )
