#!/usr/bin/env python3
"""Holder 股东数据接口详细输出示例。

单独演示 fetch_holder 的调用方式，将返回的完整内容
以表格形式输出到终端。

Usage:
    cd astock-analysis
    pip install -e ".[dev]"
    python examples/holder_detail.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["ASTOCK_CONFIG"] = os.path.join(
    os.path.dirname(__file__), "..", "config", "providers.yaml"
)

STOCK_CODE = "600519"


def pprint_holder(response: dict) -> None:
    """Pretty-print HolderResponse."""
    records = response.get("records", [])

    print("=" * 80)
    print("  HolderResponse 元信息")
    print("=" * 80)
    print(f"  provider     : {response.get('provider', '?')}")
    print(f"  code         : {response.get('code', '?')}")
    print(f"  records      : {len(records)} 条")
    print()

    print("-" * 80)
    print(f"  {'date':<16} {'holder_count':>16} {'avg_shares':>16} {'avg_value':>16}")
    print(f"  {'统计截止日':<16} {'股东户数':>16} {'户均持股':>16} {'户均市值':>16}")
    print("-" * 80)

    for r in records:
        hc = f"{r['holder_count']:>14.0f}" if r.get("holder_count") is not None else "N/A".rjust(16)
        a_s = f"{r['avg_shares']:>14.2f}" if r.get("avg_shares") is not None else "N/A".rjust(16)
        a_v = f"{r['avg_value']:>14.2f}" if r.get("avg_value") is not None else "N/A".rjust(16)
        print(f"  {r['date']:<16} {hc:>16} {a_s:>16} {a_v:>16}")

    print("=" * 80)


def main() -> None:
    from astock_analysis.dimensions.holder import fetch_holder

    print()
    print(f"  股票: {STOCK_CODE} (贵州茅台)")
    print()

    try:
        response = fetch_holder(STOCK_CODE)
        pprint_holder(response)
    except Exception as e:
        print(f"\n  [错误] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
