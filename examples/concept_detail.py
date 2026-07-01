#!/usr/bin/env python3
"""Concept 概念板块接口详细输出示例。

单独演示 fetch_concept 的调用方式，将返回的完整内容
以表格形式输出到终端。

Usage:
    cd astock-analysis
    pip install -e ".[dev]"
    python examples/concept_detail.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["ASTOCK_CONFIG"] = os.path.join(
    os.path.dirname(__file__), "..", "config", "providers.yaml"
)


def pprint_concept(response: dict) -> None:
    """Pretty-print ConceptResponse."""
    data = response.get("data", [])

    print("=" * 120)
    print("  ConceptResponse 元信息")
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

    def _trunc(v: str, width: int = 22) -> str:
        return v if len(v) <= width else v[:width - 3] + "..."

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
    from market_data.dimensions.concept import fetch_concept

    print()

    # ── 模式1: 列出所有概念板块 ──
    print("【模式1】列出所有概念板块")
    try:
        response = fetch_concept()
        pprint_concept(response)
    except Exception as e:
        print(f"\n  [错误] {e}")

    # ── 模式2: 查询具体概念板块历史 ──
    print("\n【模式2】查询「人工智能」概念板块历史行情（最近5条）")
    try:
        response = fetch_concept(board_name="人工智能")
        data = response.get("data", [])
        print(f"  provider  : {response.get('provider', '?')}")
        print(f"  board_name: {response.get('board_name', '?')}")
        print(f"  records   : {len(data)} 条")
        if data:
            keys = list(data[0].keys())
            for row in data[-5:]:
                print("  ", {k: row.get(k) for k in keys})
    except Exception as e:
        print(f"\n  [错误] {e}")

    print()


if __name__ == "__main__":
    main()
