#!/usr/bin/env python3
"""LHB 龙虎榜接口详细输出示例。

按日期组织：先展示当日总榜，再展示营业部席位明细。

Usage:
    cd astock-analysis
    pip install -e ".[dev]"
    python examples/lhb_detail.py
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["ASTOCK_CONFIG"] = os.path.join(
    os.path.dirname(__file__), "..", "config", "providers.yaml"
)

STOCK_CODE = "600105"
START_DATE = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
END_DATE = datetime.now().strftime("%Y-%m-%d")


def pprint_day_summary(row: dict) -> None:
    """Print a one-line day summary from an LHB record."""
    price = row.get("收盘价", "?")
    change = row.get("涨跌幅", 0) or 0
    net_buy = row.get("龙虎榜净买额", 0) or 0
    turnover = row.get("换手率", 0) or 0
    reason = row.get("上榜原因", "?")

    arrow = "+" if float(change) >= 0 else ""
    print(f"  收盘价: {price}  |  涨跌幅: {arrow}{change}%  |  "
          f"龙虎榜净买额: {net_buy:,.2f}  |  换手率: {turnover}%")
    print(f"  上榜原因: {reason}")


def pprint_lhb_detail(desks: list[dict]) -> None:
    """Pretty-print trading desk detail table."""
    if not desks:
        print("  (无营业部席位数据)")
        print()
        return

    keys = ["desk_name", "buy_amount", "buy_pct", "sell_amount", "sell_pct", "net_amount"]
    labels = {
        "desk_name": "营业部名称",
        "buy_amount": "买入金额",
        "buy_pct": "买入占比",
        "sell_amount": "卖出金额",
        "sell_pct": "卖出占比",
        "net_amount": "净额",
    }
    key_widths = {k: max(len(labels[k]), 14) for k in keys}
    for row in desks:
        for k in keys:
            if k != "desk_name":
                v = row.get(k, "")
                if v is not None and v != "":
                    v = f"{float(v):,.2f}"
                else:
                    v = "-"
            else:
                v = str(row.get(k, ""))
            key_widths[k] = max(key_widths[k], len(v))

    header = "  " + "  ".join(f"{labels[k]:>{key_widths[k]}}" for k in keys)
    sep = "  " + "  ".join("-" * key_widths[k] for k in keys)

    print(f"  席位明细 ({len(desks)} 个):")
    print(sep)
    print(header)
    print(sep)
    for row in desks:
        vals = []
        for k in keys:
            v = row.get(k, "")
            if k != "desk_name":
                if v is not None and v != "":
                    v = f"{float(v):,.2f}"
                else:
                    v = "-"
            vals.append(f"{str(v):>{key_widths[k]}}")
        print("  " + "  ".join(vals))
    print(sep)

    total_buy = sum(r.get("buy_amount", 0) or 0 for r in desks)
    total_sell = sum(r.get("sell_amount", 0) or 0 for r in desks)
    total_net = sum(r.get("net_amount", 0) or 0 for r in desks)
    print(f"  买入合计: {total_buy:,.2f}  卖出合计: {total_sell:,.2f}  "
          f"净额合计: {total_net:,.2f}")
    print()


def main() -> None:
    from market_data.dimensions.lhb import fetch_lhb, fetch_lhb_detail

    print()
    print(f"  股票: {STOCK_CODE} (永鼎股份)")
    print(f"  区间: {START_DATE} → {END_DATE}")
    print()

    try:
        response = fetch_lhb(code=STOCK_CODE, start_date=START_DATE, end_date=END_DATE)
    except Exception as e:
        print(f"\n  [错误] fetch_lhb: {e}")
        sys.exit(1)

    data = response.get("data", [])
    if not data:
        print("  (无数据 - 该股票近期未上龙虎榜)")
        return

    print(f"  共 {len(data)} 个龙虎榜交易日")
    print()

    for i, row in enumerate(data, 1):
        date_str = str(row.get("上榜日", ""))[:10]
        print("=" * 100)
        print(f"  [{i}] {date_str}")
        print("-" * 100)
        pprint_day_summary(row)
        print()

        try:
            detail = fetch_lhb_detail(code=STOCK_CODE, date=date_str)
            pprint_lhb_detail(detail.get("desks", []))
        except Exception as e:
            print(f"  [警告] 席位明细获取失败: {e}")
            print()

    print("=" * 100)


if __name__ == "__main__":
    main()
