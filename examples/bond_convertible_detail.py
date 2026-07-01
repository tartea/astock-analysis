#!/usr/bin/env python3
"""Bond convertible 可转债接口详细输出示例。

单独演示 fetch_bond_convertible 的调用方式，将返回的完整内容
以表格形式输出到终端。

Usage:
    cd astock-analysis
    pip install -e ".[dev]"
    python examples/bond_convertible_detail.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["ASTOCK_CONFIG"] = os.path.join(
    os.path.dirname(__file__), "..", "config", "providers.yaml"
)


def pprint_bond_convertible(response: dict) -> None:
    """Pretty-print BondConvertibleResponse."""
    data = response.get("data", [])

    print("=" * 120)
    print("  BondConvertibleResponse 元信息")
    print("=" * 120)
    print(f"  provider : {response.get('provider', '?')}")
    print(f"  records  : {len(data)} 条")
    print()

    if not data:
        print("  (无数据)")
        print("=" * 120)
        return

    keys = list(data[0].keys())

    def _trunc(v: str, width: int = 22) -> str:
        return v if len(v) <= width else v[:width-3] + "..."

    col_widths = {k: max(len(str(k)), 12) for k in keys}
    for row in data:
        for k in keys:
            v = str(row.get(k, ""))
            col_widths[k] = max(col_widths.get(k, 12), min(len(v), 24))

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
            f"{_trunc(str(row.get(k, '')), col_widths[k]):>{col_widths[k]}}" for k in keys
        )
        print(line)
    print(sep)
    print("=" * 120)


def main() -> None:
    from market_data.dimensions.bond_convertible import fetch_bond_convertible

    print()

    try:
        response = fetch_bond_convertible()
        pprint_bond_convertible(response)
    except Exception as e:
        print(f"\n  [错误] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
