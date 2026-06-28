"""Holder dimension router.

Provides a unified interface for fetching shareholder structure data.

Usage:
    from astock_analysis.dimensions.holder import fetch_holder, fetch_top_holders

    response = fetch_holder("600519")
    for r in response['records'][:3]:
        print(f"  {r['date']} holders={r['holder_count']}")

    top = fetch_top_holders("600519")
    for r in top['records'][:5]:
        print(f"  #{r['rank']} {r['holder_name']} {r['share_ratio']}%")
"""

from __future__ import annotations

import logging
from datetime import date as date_type

import pandas as pd

from astock_analysis.core.chain import try_chain, register_provider, ProviderError
from astock_analysis.core.config import get_config
from astock_analysis.core.cache import TTL_QUARTERLY
from astock_analysis.providers.akshare import provider as akshare_provider

from .types import HolderRecord, HolderResponse, TopHolderRecord, TopHolderResponse

logger = logging.getLogger(__name__)

register_provider("akshare", akshare_provider)

_QUARTER_ENDS = ("0331", "0630", "0930", "1231")


def _recent_quarter_ends(n: int) -> list[str]:
    """Return the N most recent quarter-end dates as YYYYMMDD strings."""
    today = date_type.today()
    result: list[str] = []
    y = today.year
    while len(result) < n:
        for qe in reversed(_QUARTER_ENDS):
            d = date_type(y, int(qe[:2]), int(qe[2:]))
            if d < today:
                result.append(f"{y}{qe}")
                if len(result) >= n:
                    break
        y -= 1
    return result


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


def _build_top_records(df: pd.DataFrame) -> list[TopHolderRecord]:
    """Convert a DataFrame to TopHolderRecord list."""
    records: list[TopHolderRecord] = []
    for _, row in df.iterrows():
        records.append(
            TopHolderRecord(
                rank=int(row["rank"]) if pd.notna(row.get("rank")) else 0,
                holder_name=str(row.get("holder_name", "")),
                holder_nature=str(row["holder_nature"]) if pd.notna(row.get("holder_nature")) else None,
                share_type=str(row.get("share_type", "")),
                share_num=float(row["share_num"]) if pd.notna(row.get("share_num")) else None,
                share_ratio=float(row["share_ratio"]) if pd.notna(row.get("share_ratio")) else None,
                share_change=str(row.get("share_change", "")),
                change_ratio=float(row["change_ratio"]) if pd.notna(row.get("change_ratio")) else None,
                report_date=str(row.get("report_date", "")),
            )
        )
    return records


def fetch_top_holders(
    code: str,
    date: str | None = None,
    free: bool = True,
    periods: int = 3,
    use_cache: bool = True,
) -> TopHolderResponse:
    """Fetch major shareholders for recent periods (十大股东 / 十大流通股东).

    Args:
        code: A-share stock code (e.g. '600519').
        date: Report date as 'YYYYMMDD'. If None, uses the N most recent quarter ends.
        free: True for 十大流通股东, False for 十大股东.
        periods: Number of periods to fetch (default 3).
        use_cache: Whether to use the cache layer.

    Returns:
        TopHolderResponse with records from all fetched periods.
    """
    config = get_config()
    cache_ttl = TTL_QUARTERLY if use_cache else None

    if date:
        dates = [date]
    else:
        dates = _recent_quarter_ends(periods)

    all_records: list[TopHolderRecord] = []
    provider_name = ""
    fetched_dates: list[str] = []

    for d in dates:
        try:
            df, provider_name = try_chain(
                method_name="fetch_top_holders",
                dimension="holder",
                code=code,
                ticker=code,
                cache_ttl=cache_ttl,
                config=config,
                date=d,
                free=free,
            )
            if not isinstance(df, pd.DataFrame):
                logger.warning("Provider '%s' returned %s for date=%s, skipping", provider_name, type(df).__name__, d)
                continue
            fetched_dates.append(d)
            all_records.extend(_build_top_records(df))
        except Exception as e:
            logger.warning("Failed to fetch top_holders for %s date=%s: %s", code, d, e)
            continue

    if not all_records:
        raise ProviderError(f"No top_holders data found for {code}")

    return TopHolderResponse(
        records=all_records,
        provider=provider_name,
        code=code,
        date=",".join(fetched_dates),
        holder_type="free_top10" if free else "top10",
    )
