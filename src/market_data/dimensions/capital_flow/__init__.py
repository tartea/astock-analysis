"""Capital flow dimension router.

Provides a unified interface for fetching individual stock fund flow data.

Usage:
    from market_data.dimensions.capital_flow import fetch_capital_flow

    response = fetch_capital_flow("600519")
    for r in response['records'][:3]:
        print(f"  {r['date']} main_net={r['main_net_inflow']}")
"""

from __future__ import annotations

import pandas as pd

from market_data.core.chain import try_chain, register_provider, ProviderError
from market_data.core.config import get_config
from market_data.core.cache import TTL_INTRADAY
from market_data.providers.akshare import provider as akshare_provider

from .types import CapitalFlowRecord, CapitalFlowResponse

register_provider("akshare", akshare_provider)


def fetch_capital_flow(code: str, use_cache: bool = True) -> CapitalFlowResponse:
    """Fetch individual stock capital flow data.

    Args:
        code: A-share stock code (e.g. '600519')
        use_cache: Whether to use the cache layer (default True)

    Returns:
        CapitalFlowResponse with records list and metadata.
    """
    config = get_config()
    cache_ttl = TTL_INTRADAY if use_cache else None

    df, provider_name = try_chain(
        method_name="fetch_capital_flow",
        dimension="capital_flow",
        code=code,
        ticker=code,
        cache_ttl=cache_ttl,
        config=config,
    )

    if not isinstance(df, pd.DataFrame):
        raise ProviderError(
            f"Provider '{provider_name}' returned {type(df).__name__} instead of DataFrame"
        )

    records: list[CapitalFlowRecord] = []
    for _, row in df.iterrows():
        records.append(
            CapitalFlowRecord(
                date=str(row.get("date", "")),
                main_net_inflow=float(row["main_net_inflow"]) if pd.notna(row.get("main_net_inflow")) else None,
                main_net_pct=float(row["main_net_pct"]) if pd.notna(row.get("main_net_pct")) else None,
                super_large_net=float(row["super_large_net"]) if pd.notna(row.get("super_large_net")) else None,
                super_large_pct=float(row["super_large_pct"]) if pd.notna(row.get("super_large_pct")) else None,
                large_net=float(row["large_net"]) if pd.notna(row.get("large_net")) else None,
                large_pct=float(row["large_pct"]) if pd.notna(row.get("large_pct")) else None,
                medium_net=float(row["medium_net"]) if pd.notna(row.get("medium_net")) else None,
                medium_pct=float(row["medium_pct"]) if pd.notna(row.get("medium_pct")) else None,
                small_net=float(row["small_net"]) if pd.notna(row.get("small_net")) else None,
                small_pct=float(row["small_pct"]) if pd.notna(row.get("small_pct")) else None,
            )
        )

    return CapitalFlowResponse(
        records=records,
        provider=provider_name,
        code=code,
    )
