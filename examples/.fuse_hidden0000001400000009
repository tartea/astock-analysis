#!/usr/bin/env python3
"""Realtime 行情接口详细输出示例。

单独演示 fetch_realtime 的调用方式，将返回的完整内容
以 key-value 形式输出。

Usage:
    cd astock-analysis
    pip install -e ".[dev]"
    python examples/realtime_detail.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["ASTOCK_CONFIG"] = os.path.join(
    os.path.dirname(__file__), "..", "config", "providers.yaml"
)

STOCK_CODE = "600519"


def pprint_realtime(response: dict) -> None:
    """Pretty-print RealtimeResponse."""
    print("=" * 60)
    print("  RealtimeResponse - 实时行情")
    print("=" * 60)

    fields = [
        ("code", "股票代码"),
        ("name", "股票名称"),
        ("price", "最新价"),
        ("open", "今开"),
        ("high", "最高"),
        ("low", "最低"),
        ("volume", "成交量"),
        ("amount", "成交额"),
        ("change", "涨跌额"),
        ("pct_chg", "涨跌幅(%)"),
        ("turnover", "换手率(%)"),
        ("pe", "市盈率(动态)"),
        ("pb", "市净率"),
        ("total_mv", "总市值"),
        ("circ_mv", "流通市值"),
        ("provider", "数据源"),
    ]

    for key, label in fields:
        val = response.get(key)
        if isinstance(val, float):
            if key in ("total_mv", "circ_mv", "amount"):
                print(f"  {label:12s} : {val:>15.2f}  (元)")
            elif key in ("pe", "pb"):
                print(f"  {label:12s} : {val:>15.2f}" if val is not None else f"  {label:12s} : {'N/A':>15}")
            else:
                print(f"  {label:12s} : {val:>15.2f}")
        else:
            print(f"  {label:12s} : {val}")

    print("=" * 60)


def main() -> None:
    from astock_analysis.dimensions.realtime import fetch_realtime

    print()
    print(f"  股票: {STOCK_CODE} (贵州茅台)")
    print()

    try:
        response = fetch_realtime(STOCK_CODE)
        pprint_realtime(response)
    except Exception as e:
        print(f"\n  [错误] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
