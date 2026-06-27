#!/usr/bin/env python3
"""Capital flow 资金流向接口详细输出示例。

单独演示 fetch_capital_flow 的调用方式，将返回的完整内容
以表格形式输出到终端。

Usage:
    cd astock-analysis
    pip install -e ".[dev]"
    python examples/capital_flow_detail.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["ASTOCK_CONFIG"] = os.path.join(
    os.path.dirname(__file__), "..", "config", "providers.yaml"
)

STOCK_CODE = "600519"


def _fmt(val, width: int = 14) -> str:
    if val is None:
        return "N/A".rjust(width)
    return f"{val:>{width}.2f}"


def pprint_capital_flow(response: dict) -> None:
    """Pretty-print CapitalFlowResponse."""
    records = response.get("records", [])

    print("=" * 120)
    print("  CapitalFlowResponse 元信息")
    print("=" * 120)
    print(f"  provider : {response.get('provider', '?')}")
    print(f"  code     : {response.get('code', '?')}")
    print(f"  records  : {len(records)} 条")
    print()

    header = (
        f"  {'date':<12} {'main_net_inflow':>14} {'main_net_pct':>10}"
        f" {'super_large_net':>14} {'super_large_pct':>10}"
        f" {'large_net':>14} {'large_pct':>10}"
        f" {'medium_net':>14} {'medium_pct':>10}"
        f" {'small_net':>14} {'small_pct':>10}"
    )
    sep = "  " + "-" * (12 + 14*5 + 10*5)

    print(sep)
    print(header)
    print(sep)
    for r in records:
        line = (
            f"  {r['date']:<12}"
            f" {_fmt(r.get('main_net_inflow'))}"
            f" {_fmt(r.get('main_net_pct'), 10)}"
            f" {_fmt(r.get('super_large_net'))}"
            f" {_fmt(r.get('super_large_pct'), 10)}"
            f" {_fmt(r.get('large_net'))}"
            f" {_fmt(r.get('large_pct'), 10)}"
            f" {_fmt(r.get('medium_net'))}"
            f" {_fmt(r.get('medium_pct'), 10)}"
            f" {_fmt(r.get('small_net'))}"
            f" {_fmt(r.get('small_pct'), 10)}"
        )
        print(line)
    print(sep)
    print("=" * 120)


def main() -> None:
    from astock_analysis.dimensions.capital_flow import fetch_capital_flow

    print()
    print(f"  股票: {STOCK_CODE} (贵州茅台)")
    print()

    try:
        response = fetch_capital_flow(STOCK_CODE)
        pprint_capital_flow(response)
    except Exception as e:
        print(f"\n  [错误] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
