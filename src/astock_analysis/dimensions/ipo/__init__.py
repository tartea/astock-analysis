"""IPO dimension router.

Provides a unified interface for fetching IPO/new stock listing data.

Usage:
    from astock_analysis.dimensions.ipo import fetch_ipo

    response = fetch_ipo()
    print(f"Records: {len(response['data'])}, Provider: {response['provider']}")
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd

from astock_analysis.core.chain import try_chain, register_provider, ProviderError
from astock_analysis.core.config import get_config
from astock_analysis.core.cache import TTL_DAILY
from astock_analysis.providers.akshare import provider as akshare_provider

from .types import IPOResponse

logger = logging.getLogger(__name__)

register_provider("akshare", akshare_provider)


def compute_sector(code: str) -> str:
    """Determine 板块 (sector/board) from A-share stock code prefix."""
    code_str = str(code).strip()
    if code_str.startswith("688"):
        return "科创板"
    if code_str.startswith(("300", "301")):
        return "创业板"
    if code_str.startswith(("8", "92")):
        return "北交所"
    if code_str.startswith("002"):
        return "中小板"
    return "主板"


def _enrich_industries(records: list[dict]) -> list[dict]:
    """Resolve industry for each IPO record via fetch_stock_info.

    Uses a small thread pool for concurrent lookups. Failed lookups leave
    industry as an empty string with a warning log.
    """
    from astock_analysis.dimensions.stock_info import fetch_stock_info

    def _resolve(record: dict) -> dict:
        code = str(record.get("股票代码", ""))
        industry = ""
        if code:
            try:
                info = fetch_stock_info(code)
                industry = info.get("industry", "")
            except Exception:
                logger.warning(
                    "Failed to resolve industry for %s (%s)",
                    record.get("股票简称", code), code,
                    exc_info=True,
                )
        record["industry"] = industry
        return record

    max_workers = min(5, len(records))
    if max_workers <= 1:
        return [_resolve(r) for r in records]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_resolve, r): i for i, r in enumerate(records)}
        results: list[dict | None] = [None] * len(records)
        for future in as_completed(futures):
            idx = futures[future]
            results[idx] = future.result()
    return [r for r in results if r is not None]


def fetch_ipo(use_cache: bool = True) -> IPOResponse:
    """Fetch IPO/new stock listing data.

    Args:
        use_cache: Whether to use the cache layer (default True)

    Returns:
        IPOResponse with data list and metadata.
    """
    config = get_config()
    cache_ttl = TTL_DAILY if use_cache else None

    df, provider_name = try_chain(
        method_name="fetch_ipo",
        dimension="ipo",
        ticker="market",
        cache_ttl=cache_ttl,
        config=config,
    )

    if not isinstance(df, pd.DataFrame):
        raise ProviderError(
            f"Provider '{provider_name}' returned {type(df).__name__} instead of DataFrame"
        )

    records = df.to_dict(orient="records")
    records = [{k: (None if pd.isna(v) else v) for k, v in r.items()} for r in records]

    for r in records:
        code = str(r.get("股票代码", ""))
        r["sector"] = compute_sector(code) if code else ""

    records = _enrich_industries(records)

    return IPOResponse(
        data=records,
        provider=provider_name,
    )
