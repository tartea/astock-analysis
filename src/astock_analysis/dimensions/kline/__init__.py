"""K-line dimension router.

Provides a unified interface for fetching historical OHLCV data
regardless of which underlying provider serves it.

Usage:
    from astock_analysis.dimensions.kline import fetch_kline

    response = fetch_kline("600519", "2024-01-01", "2024-06-01")
    print(f"Served by: {response['provider']}")
    print(f"Records: {len(response['records'])}")
"""

from __future__ import annotations

from typing import Optional

from astock_analysis.core.chain import try_chain, ProviderError, register_provider
from astock_analysis.core.config import get_config
from astock_analysis.core.cache import TTL_INTRADAY
from astock_analysis.providers.akshare import provider as akshare_provider

from .types import KlineRecord, KlineResponse

# ── Register providers ─────────────────────────────────────────

register_provider("akshare", akshare_provider)


# ── Public API ─────────────────────────────────────────────────

def fetch_kline(
    code: str,
    start_date: str,
    end_date: str,
    period: str = "daily",
    adjust: str = "qfq",
    use_cache: bool = True,
) -> KlineResponse:
    """Fetch historical K-line data for an A-share stock.

    Iterates through configured providers (from providers.yaml) in
    priority order. On failure, falls back to the next provider.

    Args:
        code: A-share stock code (e.g. '600519')
        start_date: Start date 'YYYY-MM-DD' or 'YYYYMMDD'
        end_date: End date 'YYYY-MM-DD' or 'YYYYMMDD'
        period: 'daily', 'weekly', or 'monthly'
        adjust: 'qfq' (forward-adjusted), 'hfq' (backward), '' (none)
        use_cache: Whether to use the cache layer (default True)

    Returns:
        KlineResponse with records list and metadata.

    Raises:
        AllProvidersFailedError: When no provider can serve the request.
    """
    config = get_config()
    cache_ttl = TTL_INTRADAY if use_cache else None

    df, provider_name = try_chain(
        method_name="fetch_kline",
        dimension="kline",
        code=code,
        start_date=start_date,
        end_date=end_date,
        period=period,
        adjust=adjust,
        ticker=code,
        cache_ttl=cache_ttl,
        config=config,
    )

    import pandas as pd

    if not isinstance(df, pd.DataFrame):
        raise ProviderError(
            f"Provider '{provider_name}' returned {type(df).__name__} instead of DataFrame"
        )

    # Convert DataFrame to list of KlineRecord dicts
    records: list[KlineRecord] = []
    for _, row in df.iterrows():
        records.append(
            KlineRecord(
                date=str(row.get("date", "")),
                open=float(row.get("open", 0)),
                high=float(row.get("high", 0)),
                low=float(row.get("low", 0)),
                close=float(row.get("close", 0)),
                volume=float(row.get("volume", 0)),
                amount=float(row.get("amount", 0)),
                pct_chg=float(row["pct_chg"]) if pd.notna(row.get("pct_chg")) else None,
            )
        )

    return KlineResponse(
        records=records,
        provider=provider_name,
        code=code,
        start_date=start_date,
        end_date=end_date,
    )
