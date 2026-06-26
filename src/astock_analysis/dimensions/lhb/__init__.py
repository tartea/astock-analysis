"""LHB (龙虎榜) dimension router.

Provides a unified interface for fetching Dragon-Tiger Board data.

Usage:
    from astock_analysis.dimensions.lhb import fetch_lhb

    response = fetch_lhb(code="600519")
    print(f"Records: {len(response['data'])}, Provider: {response['provider']}")
"""

from __future__ import annotations

import pandas as pd

from astock_analysis.core.chain import try_chain, register_provider, ProviderError
from astock_analysis.core.config import get_config
from astock_analysis.core.cache import TTL_DAILY
from astock_analysis.providers.akshare import provider as akshare_provider

from .types import LHBResponse

register_provider("akshare", akshare_provider)


def fetch_lhb(
    code: str = "",
    start_date: str = "",
    end_date: str = "",
    use_cache: bool = True,
) -> LHBResponse:
    """Fetch Dragon-Tiger Board (龙虎榜) data.

    Args:
        code: Optional stock code filter
        start_date: Start date 'YYYY-MM-DD'
        end_date: End date 'YYYY-MM-DD'
        use_cache: Whether to use the cache layer (default True)

    Returns:
        LHBResponse with data list and metadata.
    """
    config = get_config()
    cache_ttl = TTL_DAILY if use_cache else None

    df, provider_name = try_chain(
        method_name="fetch_lhb",
        dimension="lhb",
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
    return LHBResponse(
        data=[{k: (None if pd.isna(v) else v) for k, v in r.items()} for r in records],
        provider=provider_name,
        code=code,
    )
