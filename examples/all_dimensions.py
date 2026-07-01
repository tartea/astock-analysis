#!/usr/bin/env python3
"""Complete demo: exercise all 19 dimensions via the market_data framework.

Each dimension is called once, the result is inspected, and a compact summary
is printed to stdout.  Network failures are caught gracefully so the script
always completes — you can see which dimensions succeeded and which need
network / akshare.

Usage:
    cd astock-analysis
    pip install -e ".[dev]"
    python examples/all_dimensions.py
"""

from __future__ import annotations

import os
import sys
import textwrap
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

# Ensure the package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["ASTOCK_CONFIG"] = os.path.join(
    os.path.dirname(__file__), "..", "config", "providers.yaml"
)

STOCK_CODE = "600519"       # 贵州茅台 — stable, high liquidity
INDEX_CODE = "000001"       # 上证指数
START_DATE = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
END_DATE = datetime.now().strftime("%Y-%m-%d")

# ── helpers ──────────────────────────────────────────────────────────────────

def _ok(msg: str) -> str:    return f"\033[92m{msg}\033[0m"   # green
def _warn(msg: str) -> str:  return f"\033[93m{msg}\033[0m"   # yellow
def _bold(msg: str) -> str:  return f"\033[1m{msg}\033[0m"

def _call(label: str, fn, *args, **kwargs) -> Optional[Dict[str, Any]]:
    """Call *fn*, print a one-line summary, return the raw result dict."""
    print(f"  {_bold(label):<30s} ", end="", flush=True)
    try:
        result = fn(*args, **kwargs)
    except Exception as exc:
        print(_warn(f"SKIP — {exc}"))
        return None

    if isinstance(result, dict):
        summary = _summarise_dict(label, result)
    else:
        summary = f"type={type(result).__name__}"

    print(_ok(f"OK  — {summary}"))
    return result


def _summarise_dict(label: str, d: dict) -> str:
    """Build a compact one-line summary of a dimension response dict."""
    parts: list[str] = []
    provider = d.get("provider", "?")
    parts.append(f"provider={provider}")

    if "records" in d:
        parts.append(f"records={len(d['records'])}")
        if d["records"] and isinstance(d["records"][0], dict):
            first_keys = list(d["records"][0].keys())[:3]
            parts.append(f"fields=[{','.join(first_keys)}...]")
    elif "data" in d:
        parts.append(f"rows={len(d['data'])}")
        if d["data"] and isinstance(d["data"][0], dict):
            first_keys = list(d["data"][0].keys())[:3]
            parts.append(f"fields=[{','.join(first_keys)}...]")

    if label == "realtime" and "price" in d:
        parts.append(f"price={d['price']}")
    if label == "sentiment" and "market_sentiment" in d:
        parts.append(f"mood={d['market_sentiment']}")
    if label == "stock_info" and "name" in d:
        parts.append(f"name={d['name']}")
    return "  ".join(parts)


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    from market_data.core.config import get_config
    from market_data.core.cache import cache_stats

    config = get_config()
    dims = sorted(config.dimensions.keys())

    print("=" * 72)
    print(" astock-analysis — all 19 dimensions demo")
    print("=" * 72)
    print(f" Stock: {STOCK_CODE}  |  Index: {INDEX_CODE}")
    print(f" Period: {START_DATE} → {END_DATE}")
    print(f" Dimensions configured: {len(dims)}")
    print()

    ok_count = 0
    skip_count = 0

    # ── 1. kline ──────────────────────────────────────────────────
    from market_data.dimensions.kline import fetch_kline
    r = _call("1. kline (K线)", fetch_kline, STOCK_CODE, START_DATE, END_DATE)
    ok_count += 1 if r else 0; skip_count += 0 if r else 1  # pyright: ignore

    # ── 2. realtime ──────────────────────────────────────────────
    from market_data.dimensions.realtime import fetch_realtime
    r = _call("2. realtime (实时行情)", fetch_realtime, STOCK_CODE)
    ok_count += 1 if r else 0; skip_count += 0 if r else 1  # pyright: ignore

    # ── 3. index ─────────────────────────────────────────────────
    from market_data.dimensions.index import fetch_index
    r = _call("3. index (指数)", fetch_index, INDEX_CODE, START_DATE, END_DATE)
    ok_count += 1 if r else 0; skip_count += 0 if r else 1  # pyright: ignore

    # ── 4. financials ────────────────────────────────────────────
    from market_data.dimensions.financials import fetch_financials
    r = _call("4. financials (财务数据)", fetch_financials, STOCK_CODE)
    ok_count += 1 if r else 0; skip_count += 0 if r else 1  # pyright: ignore

    # ── 5. stock_info ────────────────────────────────────────────
    from market_data.dimensions.stock_info import fetch_stock_info
    r = _call("5. stock_info (基本信息)", fetch_stock_info, STOCK_CODE)
    ok_count += 1 if r else 0; skip_count += 0 if r else 1  # pyright: ignore

    # ── 6. holder ────────────────────────────────────────────────
    from market_data.dimensions.holder import fetch_holder
    r = _call("6. holder (股东数据)", fetch_holder, STOCK_CODE)
    ok_count += 1 if r else 0; skip_count += 0 if r else 1  # pyright: ignore

    # ── 7. capital_flow ──────────────────────────────────────────
    from market_data.dimensions.capital_flow import fetch_capital_flow
    r = _call("7. capital_flow (资金流向)", fetch_capital_flow, STOCK_CODE)
    ok_count += 1 if r else 0; skip_count += 0 if r else 1  # pyright: ignore

    # ── 8. north_flow ────────────────────────────────────────────
    from market_data.dimensions.north_flow import fetch_north_flow
    r = _call("8. north_flow (北向资金)", fetch_north_flow)
    ok_count += 1 if r else 0; skip_count += 0 if r else 1  # pyright: ignore

    # ── 9. margin ────────────────────────────────────────────────
    from market_data.dimensions.margin import fetch_margin
    r = _call("9. margin (融资融券)", fetch_margin, STOCK_CODE)
    ok_count += 1 if r else 0; skip_count += 0 if r else 1  # pyright: ignore

    # ── 10. lhb ──────────────────────────────────────────────────
    from market_data.dimensions.lhb import fetch_lhb
    r = _call("10. lhb (龙虎榜)", fetch_lhb, STOCK_CODE, START_DATE, END_DATE)
    ok_count += 1 if r else 0; skip_count += 0 if r else 1  # pyright: ignore

    # ── 11. block_trade ──────────────────────────────────────────
    from market_data.dimensions.block_trade import fetch_block_trade
    r = _call("11. block_trade (大宗交易)", fetch_block_trade, STOCK_CODE, START_DATE, END_DATE)
    ok_count += 1 if r else 0; skip_count += 0 if r else 1  # pyright: ignore

    # ── 12. sentiment ────────────────────────────────────────────
    from market_data.dimensions.sentiment import fetch_sentiment
    r = _call("12. sentiment (市场情绪)", fetch_sentiment)
    ok_count += 1 if r else 0; skip_count += 0 if r else 1  # pyright: ignore

    # ── 13. news ─────────────────────────────────────────────────
    from market_data.dimensions.news import fetch_news
    r = _call("13. news (新闻)", fetch_news, STOCK_CODE)
    ok_count += 1 if r else 0; skip_count += 0 if r else 1  # pyright: ignore

    # ── 14. industry ─────────────────────────────────────────────
    from market_data.dimensions.industry import fetch_industry
    r = _call("14. industry (行业板块)", fetch_industry)
    ok_count += 1 if r else 0; skip_count += 0 if r else 1  # pyright: ignore

    # ── 15. concept ──────────────────────────────────────────────
    from market_data.dimensions.concept import fetch_concept
    r = _call("15. concept (概念板块)", fetch_concept)
    ok_count += 1 if r else 0; skip_count += 0 if r else 1  # pyright: ignore

    # ── 16. fund ─────────────────────────────────────────────────
    from market_data.dimensions.fund import fetch_fund
    r = _call("16. fund (基金)", fetch_fund)
    ok_count += 1 if r else 0; skip_count += 0 if r else 1  # pyright: ignore

    # ── 17. ipo ──────────────────────────────────────────────────
    from market_data.dimensions.ipo import fetch_ipo
    r = _call("17. ipo (新股)", fetch_ipo)
    ok_count += 1 if r else 0; skip_count += 0 if r else 1  # pyright: ignore

    # ── 18. futures ──────────────────────────────────────────────
    from market_data.dimensions.futures import fetch_futures
    r = _call("18. futures (期货)", fetch_futures)
    ok_count += 1 if r else 0; skip_count += 0 if r else 1  # pyright: ignore

    # ── 19. bond_convertible ─────────────────────────────────────
    from market_data.dimensions.bond_convertible import fetch_bond_convertible
    r = _call("19. bond_convertible (可转债)", fetch_bond_convertible)
    ok_count += 1 if r else 0; skip_count += 0 if r else 1  # pyright: ignore

    print()
    print("=" * 72)
    print(f" Done.  {_ok(str(ok_count))} succeeded, {_warn(str(skip_count))} skipped")
    print()
    stats = cache_stats()
    print(" Cache stats:")
    print(f"   entries: {stats['total_entries']}  fresh: {stats['fresh_entries']}")
    print(f"   db:      {stats['db_path']}")
    print("=" * 72)


if __name__ == "__main__":
    main()
