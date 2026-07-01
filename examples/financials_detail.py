#!/usr/bin/env python3
"""Financials 财务数据接口详细输出示例。

单独演示 fetch_financials 的调用方式，将返回的完整内容
以表格形式输出到终端。

Usage:
    cd astock-analysis
    pip install -e ".[dev]"
    python examples/financials_detail.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["ASTOCK_CONFIG"] = os.path.join(
    os.path.dirname(__file__), "..", "config", "providers.yaml"
)

STOCK_CODE = "600519"


def pprint_financials(response: dict) -> None:
    """Pretty-print FinancialsResponse."""
    data = response.get("data", [])

    print("=" * 120)
    print("  FinancialsResponse 元信息")
    print("=" * 120)
    print(f"  provider : {response.get('provider', '?')}")
    print(f"  code     : {response.get('code', '?')}")
    print(f"  records  : {len(data)} 条")
    print()

    if not data:
        print("  (无数据)")
        print("=" * 120)
        return

    # Derive header from dict keys
    keys = list(data[0].keys())
    print(f"  字段列表: {keys}")
    print()

    # Determine column widths
    col_widths = {k: max(len(str(k)), 14) for k in keys}
    for row in data:
        for k in keys:
            v = str(row.get(k, ""))
            col_widths[k] = max(col_widths.get(k, 14), len(v))

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
    from market_data.dimensions.financials import fetch_financials

    print()
    print(f"  股票: {STOCK_CODE} (贵州茅台)")
    print(f"  报告期类型: 按报告期")
    print()

    try:
        response = fetch_financials(STOCK_CODE)
        pprint_financials(response)
    except Exception as e:
        print(f"\n  [错误] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
