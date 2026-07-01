"""Margin trading dimension router.

Provides a unified interface for fetching margin trading (融资融券) detail data.

Usage:
    from market_data.dimensions.margin import fetch_margin

    response = fetch_margin(code="600519")
    print(f"Records: {len(response['data'])}, Provider: {response['provider']}")
"""

from __future__ import annotations

import pandas as pd

from market_data.core.chain import try_chain, register_provider, ProviderError
from market_data.core.config import get_config
from market_data.core.cache import TTL_DAILY
from market_data.providers.akshare import provider as akshare_provider

from .types import MarginResponse

register_provider("akshare", akshare_provider)


def fetch_margin(
    code: str = "",
    start_date: str = "",
    end_date: str = "",
    use_cache: bool = True,
) -> MarginResponse:
    """Fetch margin trading (融资融券) detail data.

    Args:
        code: Optional stock code filter
        start_date: Start date 'YYYY-MM-DD' (default: 30 days ago)
        end_date: End date 'YYYY-MM-DD' (default: today)
        use_cache: Whether to use the cache layer (default True)

    Returns:
        MarginResponse with data list and metadata.
    """
    config = get_config()
    cache_ttl = TTL_DAILY if use_cache else None

    df, provider_name = try_chain(
        method_name="fetch_margin",
        dimension="margin",
        code=code,
        start_date=start_date,
        end_date=end_date,
        ticker=code or "market",
        cache_ttl=cache_ttl,
        config=config,
    )

    if not isinstance(df, pd.DataFrame):
        raise ProviderError(
            f"Provider '{provider_name}' returned {type(df).__name__} instead of DataFrame"
        )

    records = df.to_dict(orient="records")
    return MarginResponse(
        data=[{k: (None if pd.isna(v) else v) for k, v in r.items()} for r in records],
        provider=provider_name,
        code=code,
    )
