#!/usr/bin/env python3
"""Stock info 接口详细输出示例。

单独演示 fetch_stock_info 的调用方式，将返回的完整内容
以 key-value 形式输出。

Usage:
    cd astock-analysis
    pip install -e ".[dev]"
    python examples/stock_info_detail.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["ASTOCK_CONFIG"] = os.path.join(
    os.path.dirname(__file__), "..", "config", "providers.yaml"
)

STOCK_CODE = "600105"


def pprint_stock_info(response: dict) -> None:
    """Pretty-print StockInfoResponse."""
    print("=" * 60)
    print("  StockInfoResponse - 股票基本信息")
    print("=" * 60)

    fields = [
        ("code", "股票代码"),
        ("name", "股票简称"),
        ("full_name", "公司全称"),
        ("industry", "所属行业"),
        ("list_date", "上市日期"),
        ("total_shares", "总股本"),
        ("circ_shares", "流通股"),
        ("total_market_cap", "总市值"),
        ("circ_market_cap", "流通市值"),
        ("pe", "市盈率(PE)"),
        ("pb", "市净率(PB)"),
        ("eps", "每股收益(EPS)"),
        ("bvps", "每股净资产(BVPS)"),
        ("price", "最新价"),
        ("turnover", "换手率"),
        ("pct_chg", "涨跌幅"),
        ("province", "省份"),
        ("provider", "数据源"),
    ]

    for key, label in fields:
        val = response.get(key)
        if key in ("total_shares", "circ_shares", "total_market_cap", "circ_market_cap") and val is not None:
            print(f"  {label:12s} : {val:>20.2f}")
        elif key in ("pe", "pb", "eps", "bvps", "price", "turnover", "pct_chg") and val is not None:
            print(f"  {label:12s} : {val:>20.4f}")
        elif val is None:
            print(f"  {label:12s} : {'N/A':>20}")
        else:
            print(f"  {label:12s} : {val}")

    print("=" * 60)


def main() -> None:
    from market_data.dimensions.stock_info import fetch_stock_info

    print()
    print(f"  股票: {STOCK_CODE} (永鼎股份)")
    print()

    try:
        response = fetch_stock_info(STOCK_CODE)
        pprint_stock_info(response)
    except Exception as e:
        print(f"\n  [错误] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
