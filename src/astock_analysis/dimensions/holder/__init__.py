"""Holder dimension router.

Provides a unified interface for fetching shareholder structure data.

Usage:
    from astock_analysis.dimensions.holder import fetch_holder

    response = fetch_holder("600519")
    for r in response['records'][:3]:
        print(f"  {r['date']} holders={r['holder_count']}")
"""

from __future__ import annotations

import pandas as pd

from astock_analysis.core.chain import try_chain, register_provider, ProviderError
from astock_analysis.core.config import get_config
from astock_analysis.core.cache import TTL_QUARTERLY
from astock_analysis.providers.akshare import provider as akshare_provider

from .types import HolderRecord, HolderResponse

register_provider("akshare", akshare_provider)


def fetch_holder(code: str, use_cache: bool = True) -> HolderResponse:
    """Fetch shareholder structure data for an A-share stock.

    Args:
        code: A-share stock code (e.g. '600519')
        use_cache: Whether to use the cache layer (default True)

    Returns:
        HolderResponse with records list and metadata.
    """
    config = get_config()
    cache_ttl = TTL_QUARTERLY if use_cache else None

    df, provider_name = try_chain(
        method_name="fetch_holder",
        dimension="holder",
        code=code,
        ticker=code,
        cache_ttl=cache_ttl,
        config=config,
    )

    if not isinstance(df, pd.DataFrame):
        raise ProviderError(
            f"Provider '{provider_name}' returned {type(df).__name__} instead of DataFrame"
        )

    records: list[HolderRecord] = []
    for _, row in df.iterrows():
        records.append(
            HolderRecord(
                date=str(row.get("date", "")),
                holder_count=float(row["holder_count"]) if pd.notna(row.get("holder_count")) else None,
                avg_shares=float(row["avg_shares"]) if pd.notna(row.get("avg_shares")) else None,
                avg_value=float(row["avg_value"]) if pd.notna(row.get("avg_value")) else None,
            )
        )

    return HolderResponse(
        records=records,
        provider=provider_name,
        code=code,
    )
