"""Index dimension router.

Provides a unified interface for fetching index daily K-line data.

Usage:
    from market_data.dimensions.index import fetch_index

    response = fetch_index("000001")
    print(f"Records: {len(response['records'])}, Provider: {response['provider']}")
"""

from __future__ import annotations

import pandas as pd

from market_data.core.chain import try_chain, register_provider, ProviderError
from market_data.core.config import get_config
from market_data.core.cache import TTL_INTRADAY
from market_data.providers.akshare import provider as akshare_provider

from .types import IndexRecord, IndexResponse

register_provider("akshare", akshare_provider)


def fetch_index(
    code: str,
    start_date: str = "",
    end_date: str = "",
    use_cache: bool = True,
) -> IndexResponse:
    """Fetch index daily K-line data.

    Args:
        code: Index code (e.g. '000001' for SSE Composite)
        start_date: Start date 'YYYY-MM-DD', defaults to 60 days ago
        end_date: End date 'YYYY-MM-DD', defaults to today
        use_cache: Whether to use the cache layer (default True)

    Returns:
        IndexResponse with records list and metadata.
    """
    config = get_config()
    cache_ttl = TTL_INTRADAY if use_cache else None

    df, provider_name = try_chain(
        method_name="fetch_index",
        dimension="index",
        code=code,
        start_date=start_date,
        end_date=end_date,
        ticker=code,
        cache_ttl=cache_ttl,
        config=config,
    )

    if not isinstance(df, pd.DataFrame):
        raise ProviderError(
            f"Provider '{provider_name}' returned {type(df).__name__} instead of DataFrame"
        )

    records: list[IndexRecord] = []
    for _, row in df.iterrows():
        records.append(
            IndexRecord(
                date=str(row.get("date", "")),
                open=float(row.get("open", 0)),
                high=float(row.get("high", 0)),
                low=float(row.get("low", 0)),
                close=float(row.get("close", 0)),
                volume=float(row.get("volume", 0)),
                amount=float(row.get("amount", 0)),
            )
        )

    return IndexResponse(
        records=records,
        provider=provider_name,
        code=code,
        start_date=start_date,
        end_date=end_date,
    )
