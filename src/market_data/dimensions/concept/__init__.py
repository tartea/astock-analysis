"""Concept board dimension router.

Provides a unified interface for fetching concept board data.

Usage:
    from market_data.dimensions.concept import fetch_concept

    response = fetch_concept()
    print(f"Boards: {len(response['data'])}, Provider: {response['provider']}")
"""

from __future__ import annotations

import pandas as pd

from market_data.core.chain import try_chain, register_provider, ProviderError
from market_data.core.config import get_config
from market_data.core.cache import TTL_STATIC
from market_data.providers.akshare import provider as akshare_provider

from .types import ConceptResponse

register_provider("akshare", akshare_provider)


def fetch_concept(board_name: str = "", use_cache: bool = True) -> ConceptResponse:
    """Fetch concept board data.

    Args:
        board_name: Optional concept board name filter
        use_cache: Whether to use the cache layer (default True)

    Returns:
        ConceptResponse with data list and metadata.
    """
    config = get_config()
    cache_ttl = TTL_STATIC if use_cache else None

    df, provider_name = try_chain(
        method_name="fetch_concept",
        dimension="concept",
        board_name=board_name,
        ticker=board_name or "market",
        cache_ttl=cache_ttl,
        config=config,
    )

    if not isinstance(df, pd.DataFrame):
        raise ProviderError(
            f"Provider '{provider_name}' returned {type(df).__name__} instead of DataFrame"
        )

    records = df.to_dict(orient="records")
    return ConceptResponse(
        data=[{k: (None if pd.isna(v) else v) for k, v in r.items()} for r in records],
        provider=provider_name,
        board_name=board_name,
    )
