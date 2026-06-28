#!/usr/bin/env python3
"""Block trade 大宗交易接口详细输出示例。

单独演示 fetch_block_trade 的调用方式，将返回的完整内容
以表格形式输出到终端。

Usage:
    cd astock-analysis
    pip install -e ".[dev]"
    python examples/block_trade_detail.py
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["ASTOCK_CONFIG"] = os.path.join(
    os.path.dirname(__file__), "..", "config", "providers.yaml"
)

STOCK_CODE = "600105"
START_DATE = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
END_DATE = datetime.now().strftime("%Y-%m-%d")


def pprint_block_trade(response: dict) -> None:
    """Pretty-print BlockTradeResponse."""
    data = response.get("data", [])

    print("=" * 120)
    print("  BlockTradeResponse 元信息")
    print("=" * 120)
    print(f"  provider : {response.get('provider', '?')}")
    print(f"  code     : {response.get('code', '?')}")
    print(f"  records  : {len(data)} 条")
    print()

    if not data:
        print("  (无数据 - 该股票近期无大宗交易)")
        print("=" * 120)
        return

    keys = list(data[0].keys())
    col_widths = {k: max(len(str(k)), 12) for k in keys}
    for row in data:
        for k in keys:
            v = str(row.get(k, ""))
            col_widths[k] = max(col_widths.get(k, 12), len(v))

    header = "  " + "  ".join(f"{k:>{col_widths[k]}}" for k in keys)
    sep = "  " + "  ".join("-" * col_widths[k] for k in keys)

    print(sep)
    print(header)
    print(sep)
    for row in data:
        line = "  " + "  ".join(
            f"{str(row.get(k, '')):>{col_widths[k]}}" for k in keys
        )
        print(line)
    print(sep)
    print("=" * 120)


def main() -> None:
    from astock_analysis.dimensions.block_trade import fetch_block_trade

    print()
    print(f"  股票: {STOCK_CODE} (贵州茅台)")
    print(f"  区间: {START_DATE} → {END_DATE}")
    print()

    try:
        response = fetch_block_trade(code=STOCK_CODE, start_date=START_DATE, end_date=END_DATE)
        pprint_block_trade(response)
    except Exception as e:
        print(f"\n  [错误] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
