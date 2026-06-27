#!/usr/bin/env python3
"""Index 指数接口详细输出示例。

单独演示 fetch_index 的调用方式，将返回的完整内容
以表格形式输出到终端。

Usage:
    cd astock-analysis
    pip install -e ".[dev]"
    python examples/index_detail.py
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["ASTOCK_CONFIG"] = os.path.join(
    os.path.dirname(__file__), "..", "config", "providers.yaml"
)

INDEX_CODE = "000001"  # 上证指数
START_DATE = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
END_DATE = datetime.now().strftime("%Y-%m-%d")


def pprint_index(response: dict) -> None:
    """Pretty-print IndexResponse."""
    records = response.get("records", [])

    print("=" * 80)
    print("  IndexResponse 元信息")
    print("=" * 80)
    print(f"  provider  : {response.get('provider', '?')}")
    print(f"  code      : {response.get('code', '?')}")
    print(f"  start_date: {response.get('start_date', '?')}")
    print(f"  end_date  : {response.get('end_date', '?')}")
    print(f"  records   : {len(records)} 条")
    print()

    print("-" * 80)
    print(f"  {'date':<14} {'open':>10} {'high':>10} {'low':>10} {'close':>10} {'volume':>12} {'amount':>14}")
    print(f"  {'日期':<14} {'开盘':>10} {'最高':>10} {'最低':>10} {'收盘':>10} {'成交量':>12} {'成交额':>14}")
    print("-" * 80)

    for r in records:
        print(
            f"  {r['date']:<14} "
            f"{r['open']:>10.2f} "
            f"{r['high']:>10.2f} "
            f"{r['low']:>10.2f} "
            f"{r['close']:>10.2f} "
            f"{r['volume']:>12.0f} "
            f"{r['amount']:>14.0f}"
        )

    print("=" * 80)


def main() -> None:
    from astock_analysis.dimensions.index import fetch_index

    print()
    print(f"  指数: {INDEX_CODE} (上证指数)")
    print(f"  区间: {START_DATE} → {END_DATE}")
    print()

    try:
        response = fetch_index(INDEX_CODE, START_DATE, END_DATE)
        pprint_index(response)
    except Exception as e:
        print(f"\n  [错误] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
