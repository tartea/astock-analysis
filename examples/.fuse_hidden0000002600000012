#!/usr/bin/env python3
"""Margin 融资融券接口详细输出示例。

单独演示 fetch_margin 的调用方式，将返回的完整内容
以表格形式输出到终端。

默认获取最近一个月（30天）的融资融券数据。

Usage:
    cd astock-analysis
    pip install -e ".[dev]"
    python examples/margin_detail.py
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


def pprint_margin(response: dict) -> None:
    """Pretty-print MarginResponse."""
    data = response.get("data", [])

    print("=" * 120)
    print("  MarginResponse 元信息")
    print("=" * 120)
    print(f"  provider : {response.get('provider', '?')}")
    print(f"  code     : {response.get('code', '?')}")
    print(f"  records  : {len(data)} 条")
    if data:
        dates = sorted({r.get("trade_date", "?") for r in data})
        print(f"  日期范围 : {dates[0]} ~ {dates[-1]} ({len(dates)} 个交易日)")
    print()

    if not data:
        print("  (无数据)")
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
    from astock_analysis.dimensions.margin import fetch_margin

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    print()
    print(f"  股票: {STOCK_CODE} (贵州茅台)")
    print(f"  日期: {start_date} ~ {end_date}")
    print()

    try:
        response = fetch_margin(
            code=STOCK_CODE, start_date=start_date, end_date=end_date
        )
        pprint_margin(response)
    except Exception as e:
        print(f"\n  [错误] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
