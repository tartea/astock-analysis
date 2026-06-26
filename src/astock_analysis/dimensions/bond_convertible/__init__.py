"""Convertible bond dimension router.

Provides a unified interface for fetching convertible bond listing data.

Usage:
    from astock_analysis.dimensions.bond_convertible import fetch_bond_convertible

    response = fetch_bond_convertible()
    print(f"Bonds: {len(response['data'])}, Provider: {response['provider']}")
"""

from __future__ import annotations

import pandas as pd

from astock_analysis.core.chain import try_chain, register_provider, ProviderError
from astock_analysis.core.config import get_config
from astock_analysis.core.cache import TTL_DAILY
from astock_analysis.providers.akshare import provider as akshare_provider

from .types import BondConvertibleResponse

register_provider("akshare", akshare_provider)


def fetch_bond_convertible(use_cache: bool = True) -> BondConvertibleResponse:
    """Fetch convertible bond listing data.

    Args:
        use_cache: Whether to use the cache layer (default True)

    Returns:
        BondConvertibleResponse with data list and metadata.
    """
    config = get_config()
    cache_ttl = TTL_DAILY if use_cache else None

    df, provider_name = try_chain(
        method_name="fetch_bond_convertible",
        dimension="bond_convertible",
        ticker="market",
        cache_ttl=cache_ttl,
        config=config,
    )

    if not isinstance(df, pd.DataFrame):
        raise ProviderError(
            f"Provider '{provider_name}' returned {type(df).__name__} instead of DataFrame"
        )

    records = df.to_dict(orient="records")
    return BondConvertibleResponse(
        data=[{k: (None if pd.isna(v) else v) for k, v in r.items()} for r in records],
        provider=provider_name,
    )
