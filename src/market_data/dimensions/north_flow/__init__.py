"""Northbound flow dimension router.

Provides a unified interface for fetching northbound (北向资金) capital flow data.

Usage:
    from market_data.dimensions.north_flow import fetch_north_flow

    response = fetch_north_flow()
    print(f"Records: {len(response['data'])}, Provider: {response['provider']}")
"""

from __future__ import annotations

import pandas as pd

from market_data.core.chain import try_chain, register_provider, ProviderError
from market_data.core.config import get_config
from market_data.core.cache import TTL_DAILY
from market_data.providers.akshare import provider as akshare_provider

from .types import NorthFlowResponse

register_provider("akshare", akshare_provider)


def fetch_north_flow(code: str = "", use_cache: bool = True) -> NorthFlowResponse:
    """Fetch northbound (沪/深港通) capital flow data.

    Args:
        code: Optional stock code for individual stock northbound flow
        use_cache: Whether to use the cache layer (default True)

    Returns:
        NorthFlowResponse with data list and metadata.
    """
    config = get_config()
    cache_ttl = TTL_DAILY if use_cache else None

    df, provider_name = try_chain(
        method_name="fetch_north_flow",
        dimension="north_flow",
        code=code,
        ticker=code or "market",
        cache_ttl=cache_ttl,
        config=config,
    )

    if not isinstance(df, pd.DataFrame):
        raise ProviderError(
            f"Provider '{provider_name}' returned {type(df).__name__} instead of DataFrame"
        )

    records = df.to_dict(orient="records")
    return NorthFlowResponse(
        data=[{k: (None if pd.isna(v) else v) for k, v in r.items()} for r in records],
        provider=provider_name,
        code=code,
    )
