#!/usr/bin/env python3
"""Futures 期货接口详细输出示例。

单独演示 fetch_futures 的调用方式，将返回的完整内容
以表格形式输出到终端。

Usage:
    cd astock-analysis
    pip install -e ".[dev]"
    python examples/futures_detail.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["ASTOCK_CONFIG"] = os.path.join(
    os.path.dirname(__file__), "..", "config", "providers.yaml"
)

FUTURES_CODE = "IF0"  # 沪深300股指期货主力合约


def pprint_futures(response: dict) -> None:
    """Pretty-print FuturesResponse."""
    data = response.get("data", [])

    print("=" * 120)
    print("  FuturesResponse 元信息")
    print("=" * 120)
    print(f"  provider : {response.get('provider', '?')}")
    print(f"  code     : {response.get('code', '?')}")
    print(f"  records  : {len(data)} 条")
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
    for i, row in enumerate(data):
        if i >= 20:
            print(f"  ... 还有 {len(data) - 20} 条")
            break
        line = "  " + "  ".join(
            f"{str(row.get(k, '')):>{col_widths[k]}}" for k in keys
        )
        print(line)
    print(sep)
    print("=" * 120)


def main() -> None:
    from astock_analysis.dimensions.futures import fetch_futures

    print()
    print(f"  期货: {FUTURES_CODE} (沪深300股指期货主力)")
    print()

    try:
        response = fetch_futures(FUTURES_CODE)
        pprint_futures(response)
    except Exception as e:
        print(f"\n  [错误] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
