"""Financials dimension router.

Provides a unified interface for fetching financial statement data
regardless of which underlying provider serves it.

Usage:
    from astock_analysis.dimensions.financials import fetch_financials

    response = fetch_financials("600519")
    print(f"Rows: {len(response['data'])}, Provider: {response['provider']}")
"""

from __future__ import annotations

import pandas as pd

from astock_analysis.core.chain import try_chain, register_provider, ProviderError
from astock_analysis.core.config import get_config
from astock_analysis.core.cache import TTL_QUARTERLY
from astock_analysis.providers.akshare import provider as akshare_provider

from .types import FinancialsResponse

register_provider("akshare", akshare_provider)


def fetch_financials(
    code: str,
    indicator: str = "按报告期",
    use_cache: bool = True,
) -> FinancialsResponse:
    """Fetch financial statement data for an A-share stock.

    Args:
        code: A-share stock code (e.g. '600519')
        indicator: Report period — '按报告期', '按年度', '按单季度'
        use_cache: Whether to use the cache layer (default True)

    Returns:
        FinancialsResponse with data list and metadata.
    """
    config = get_config()
    cache_ttl = TTL_QUARTERLY if use_cache else None

    df, provider_name = try_chain(
        method_name="fetch_financials",
        dimension="financials",
        code=code,
        indicator=indicator,
        ticker=code,
        cache_ttl=cache_ttl,
        config=config,
    )

    if not isinstance(df, pd.DataFrame):
        raise ProviderError(
            f"Provider '{provider_name}' returned {type(df).__name__} instead of DataFrame"
        )

    records = df.to_dict(orient="records")
    return FinancialsResponse(
        data=[{k: (None if pd.isna(v) else v) for k, v in r.items()} for r in records],
        provider=provider_name,
        code=code,
    )
