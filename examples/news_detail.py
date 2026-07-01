#!/usr/bin/env python3
"""News 新闻接口详细输出示例。

单独演示 fetch_news 的调用方式，将返回的完整内容
以表格形式输出到终端。

Usage:
    cd astock-analysis
    pip install -e ".[dev]"
    python examples/news_detail.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["ASTOCK_CONFIG"] = os.path.join(
    os.path.dirname(__file__), "..", "config", "providers.yaml"
)

STOCK_CODE = "600519"


def pprint_news(response: dict) -> None:
    """Pretty-print NewsResponse."""
    data = response.get("data", [])

    print("=" * 120)
    print("  NewsResponse 元信息")
    print("=" * 120)
    print(f"  provider : {response.get('provider', '?')}")
    print(f"  code     : {response.get('code', '?')}")
    print(f"  records  : {len(data)} 条")
    print()

    if not data:
        print("  (无新闻)")
        print("=" * 120)
        return

    keys = list(data[0].keys())
    col_widths = {k: max(len(str(k)), 12) for k in keys}
    for row in data[:10]:  # show first 10
        for k in keys:
            v = str(row.get(k, ""))
            col_widths[k] = max(col_widths.get(k, 12), len(v))

    header = "  " + "  ".join(f"{k:>{col_widths[k]}}" for k in keys)
    sep = "  " + "  ".join("-" * col_widths[k] for k in keys)

    print(sep)
    print(header)
    print(sep)
    for i, row in enumerate(data):
        if i >= 10:
            print(f"  ... 还有 {len(data) - 10} 条")
            break
        line = "  " + "  ".join(
            f"{str(row.get(k, '')):>{col_widths[k]}}" for k in keys
        )
        print(line)
    print(sep)
    print("=" * 120)


def main() -> None:
    from market_data.dimensions.news import fetch_news

    print()
    print(f"  股票: {STOCK_CODE} (贵州茅台)")
    print()

    try:
        response = fetch_news(STOCK_CODE)
        pprint_news(response)
    except Exception as e:
        print(f"\n  [错误] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
