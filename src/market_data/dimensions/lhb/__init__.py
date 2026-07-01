"""LHB (龙虎榜) dimension router.

Provides a unified interface for fetching Dragon-Tiger Board data.

Usage:
    from market_data.dimensions.lhb import fetch_lhb

    response = fetch_lhb(code="600519")
    print(f"Records: {len(response['data'])}, Provider: {response['provider']}")
"""

from __future__ import annotations

import pandas as pd

from market_data.core.chain import try_chain, register_provider, ProviderError
from market_data.core.config import get_config
from market_data.core.cache import TTL_DAILY
from market_data.providers.akshare import provider as akshare_provider

from .types import LHBResponse, LHBDetailResponse

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


def fetch_lhb_detail(
    code: str,
    date: str = "",
    use_cache: bool = True,
) -> LHBDetailResponse:
    """Fetch per-trading-desk LHB detail for a stock on a given date.

    Args:
        code: A-share stock code (e.g. '600105'). Required.
        date: LHB date 'YYYY-MM-DD'. If empty, uses the latest available date.
        use_cache: Whether to use the cache layer (default True).

    Returns:
        LHBDetailResponse with desk-level records and metadata.
    """
    config = get_config()
    cache_ttl = TTL_DAILY if use_cache else None

    df, provider_name = try_chain(
        method_name="fetch_lhb_detail",
        dimension="lhb",
        code=code,
        date=date,
        ticker=code,
        cache_ttl=cache_ttl,
        config=config,
    )

    if not isinstance(df, pd.DataFrame):
        raise ProviderError(
            f"Provider '{provider_name}' returned {type(df).__name__} instead of DataFrame"
        )

    records = df.to_dict(orient="records")
    clean = [{k: (None if pd.isna(v) else v) for k, v in r.items()} for r in records]
    resolved_date = date or df.attrs.get("date", "")

    return LHBDetailResponse(
        desks=clean,
        provider=provider_name,
        code=code,
        date=resolved_date if isinstance(resolved_date, str) else str(resolved_date),
    )
