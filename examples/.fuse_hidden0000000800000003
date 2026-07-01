#!/usr/bin/env python3
"""MVP example: fetch K-line data using the astock_analysis framework.

This demonstrates the full flow:
1. Configuration loading from providers.yaml
2. Provider registration
3. try_chain failover engine
4. SQLite cache layer
5. TypedDict response

Usage:
    cd astock-analysis
    pip install -e .
    python examples/basic_usage.py
"""

import os
import sys
from datetime import datetime, timedelta

# Ensure the package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Point config loader to our local config file
os.environ["ASTOCK_CONFIG"] = os.path.join(
    os.path.dirname(__file__), "..", "config", "providers.yaml"
)


def main():
    from astock_analysis.dimensions.kline import fetch_kline
    from astock_analysis.core.config import get_config
    from astock_analysis.core.cache import cache_stats

    # ── Show loaded config ──────────────────────────────────────
    config = get_config()
    print("=" * 60)
    print("Configuration loaded:")
    print(f"  Providers: {list(config.providers.keys())}")
    print(f"  Dimensions: {list(config.dimensions.keys())}")
    print(f"  Cache enabled: {config.cache_enabled}")
    dim = config.get_dimension("kline")
    if dim:
        print(f"  kline providers: {dim.providers}")
    print()

    # ── Fetch K-line data ───────────────────────────────────────
    code = "600519"  # 贵州茅台
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    print(f"Fetching kline for {code} ({start_date} → {end_date})...")
    print()

    try:
        response = fetch_kline(code, start_date, end_date)
    except Exception as e:
        print(f"ERROR: {e}")
        print()
        print("Make sure akshare is installed:")
        print("  pip install akshare")
        sys.exit(1)

    # ── Display results ─────────────────────────────────────────
    print(f"Provider: {response['provider']}")
    print(f"Code:     {response['code']}")
    print(f"Period:   {response['start_date']} → {response['end_date']}")
    print(f"Records:  {len(response['records'])}")
    print()

    # Show first 3 and last 3 records
    records = response["records"]
    if records:
        print(f"{'Date':<12} {'Open':>8} {'High':>8} {'Low':>8} {'Close':>8} {'Vol':>12} {'Chg%':>8}")
        print("-" * 72)
        for r in records[:3]:
            pct = f"{r['pct_chg']:.2f}" if r["pct_chg"] is not None else "N/A"
            print(
                f"{r['date']:<12} {r['open']:>8.2f} {r['high']:>8.2f} "
                f"{r['low']:>8.2f} {r['close']:>8.2f} {r['volume']:>12.0f} {pct:>8}"
            )
        if len(records) > 6:
            print(f"{'...':<12} {'...':>8} {'...':>8} {'...':>8} {'...':>8} {'...':>12} {'...':>8}")
        for r in records[-3:]:
            pct = f"{r['pct_chg']:.2f}" if r["pct_chg"] is not None else "N/A"
            print(
                f"{r['date']:<12} {r['open']:>8.2f} {r['high']:>8.2f} "
                f"{r['low']:>8.2f} {r['close']:>8.2f} {r['volume']:>12.0f} {pct:>8}"
            )
    print()

    # ── Cache stats ─────────────────────────────────────────────
    stats = cache_stats()
    print("Cache stats:")
    print(f"  Total entries: {stats['total_entries']}")
    print(f"  Fresh entries: {stats['fresh_entries']}")
    print(f"  DB path:       {stats['db_path']}")
    print()

    # ── Second call — should hit cache ──────────────────────────
    print("Second call (should hit cache)...")
    response2 = fetch_kline(code, start_date, end_date)
    print(f"  Records: {len(response2['records'])} (from cache)")
    print()

    print("=" * 60)
    print("MVP demo complete. The framework is working!")
    print()
    print("Next steps:")
    print("  1. Add more providers (tushare, efinance, baostock)")
    print("  2. Add more dimensions (realtime, financials, sentiment, ...)")
    print("  3. Run: pytest tests/")


if __name__ == "__main__":
    main()
