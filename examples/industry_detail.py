#!/usr/bin/env python3
"""Industry 行业板块接口详细输出示例。

单独演示 fetch_industry 的调用方式，将返回的完整内容
以表格形式输出到终端。

Usage:
    cd astock-analysis
    pip install -e ".[dev]"
    python examples/industry_detail.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["ASTOCK_CONFIG"] = os.path.join(
    os.path.dirname(__file__), "..", "config", "providers.yaml"
)


def pprint_industry(response: dict) -> None:
    """Pretty-print IndustryResponse."""
    data = response.get("data", [])

    print("=" * 120)
    print("  IndustryResponse 元信息")
    print("=" * 120)
    print(f"  provider  : {response.get('provider', '?')}")
    print(f"  board_name: {response.get('board_name', '?')}")
    print(f"  records   : {len(data)} 条")
    print()

    if not data:
        print("  (无数据)")
        print("=" * 120)
        return

    keys = list(data[0].keys())

    # Truncate long string values for cleaner display
    def _trunc(v: str, width: int = 20) -> str:
        return v if len(v) <= width else v[:width-3] + "..."

    col_widths = {k: max(len(str(k)), 12) for k in keys}
    for row in data:
        for k in keys:
            v = str(row.get(k, ""))
            col_widths[k] = max(col_widths.get(k, 12), min(len(v), 22))

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
    from astock_analysis.dimensions.industry import fetch_industry

    print()

    try:
        response = fetch_industry()
        pprint_industry(response)
    except Exception as e:
        print(f"\n  [错误] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
