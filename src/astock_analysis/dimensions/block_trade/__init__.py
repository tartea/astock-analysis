"""Block trade dimension router.

Provides a unified interface for fetching block trade (大宗交易) data.

Usage:
    from astock_analysis.dimensions.block_trade import fetch_block_trade

    response = fetch_block_trade(code="600519")
    print(f"Records: {len(response['data'])}, Provider: {response['provider']}")
"""

from __future__ import annotations

import pandas as pd

from astock_analysis.core.chain import try_chain, register_provider, ProviderError
from astock_analysis.core.config import get_config
from astock_analysis.core.cache import TTL_DAILY
from astock_analysis.providers.akshare import provider as akshare_provider

from .types import BlockTradeResponse

register_provider("akshare", akshare_provider)


def fetch_block_trade(
    code: str = "",
    start_date: str = "",
    end_date: str = "",
    use_cache: bool = True,
) -> BlockTradeResponse:
    """Fetch block trade (大宗交易) data.

    Args:
        code: Optional stock code filter
        start_date: Start date 'YYYY-MM-DD'
        end_date: End date 'YYYY-MM-DD'
        use_cache: Whether to use the cache layer (default True)

    Returns:
        BlockTradeResponse with data list and metadata.
    """
    config = get_config()
    cache_ttl = TTL_DAILY if use_cache else None

    df, provider_name = try_chain(
        method_name="fetch_block_trade",
        dimension="block_trade",
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
    return BlockTradeResponse(
        data=[{k: (None if pd.isna(v) else v) for k, v in r.items()} for r in records],
        provider=provider_name,
        code=code,
    )
