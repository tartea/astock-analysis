#!/usr/bin/env python3
"""K-line 接口详细输出示例。

单独演示 fetch_kline 的调用方式，并将返回的完整内容
以表格形式输出到终端，方便查看每条 K 线记录的详情。

Usage:
    cd astock-analysis
    pip install -e ".[dev]"
    python examples/kline_detail.py
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["ASTOCK_CONFIG"] = os.path.join(
    os.path.dirname(__file__), "..", "config", "providers.yaml"
)

STOCK_CODE = "600105"  # 贵州茅台
START_DATE = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
END_DATE = datetime.now().strftime("%Y-%m-%d")


def pprint_kline_response(response: dict) -> None:
    """Pretty-print a KlineResponse in full detail."""
    # ── 元信息 ──
    print("=" * 80)
    print("  KlineResponse 元信息")
    print("=" * 80)
    print(f"  provider  : {response.get('provider', '?')}")
    print(f"  code      : {response.get('code', '?')}")
    print(f"  start_date: {response.get('start_date', '?')}")
    print(f"  end_date  : {response.get('end_date', '?')}")
    print(f"  records   : {len(response.get('records', []))} 条")
    print()

    # ── 字段说明 ──
    print("-" * 80)
    print("  字段说明:")
    print(f"  {'date':<14} {'open':>8} {'high':>8} {'low':>8} {'close':>8} {'volume':>12} {'amount':>14} {'pct_chg':>8}")
    print(f"  {'日期':<14} {'开盘':>8} {'最高':>8} {'最低':>8} {'收盘':>8} {'成交量':>12} {'成交额(元)':>14} {'涨跌幅%':>8}")
    print("-" * 80)

    # ── 逐条输出 ──
    records = response.get("records", [])
    for i, r in enumerate(records, 1):
        print(
            f"  {r['date']:<14} "
            f"{r['open']:>8.2f} "
            f"{r['high']:>8.2f} "
            f"{r['low']:>8.2f} "
            f"{r['close']:>8.2f} "
            f"{r['volume']:>12.0f} "
            f"{r['amount']:>14.0f} "
            f"{r['pct_chg']:>8.2f}" if r['pct_chg'] is not None else f"{'N/A':>8}"
        )

    print("=" * 80)

    # ── 统计信息 ──
    if records:
        closes = [r["close"] for r in records]
        volumes = [r["volume"] for r in records]
        pct_chgs = [r["pct_chg"] for r in records if r["pct_chg"] is not None]
        print()
        print("  统计摘要:")
        print(f"    收盘价范围 : {min(closes):.2f} ~ {max(closes):.2f}")
        print(f"    收盘均价   : {sum(closes)/len(closes):.2f}")
        print(f"    总成交量   : {sum(volumes):.0f}")
        if pct_chgs:
            up = sum(1 for p in pct_chgs if p > 0)
            down = sum(1 for p in pct_chgs if p < 0)
            flat = sum(1 for p in pct_chgs if p == 0)
            print(f"    涨跌分布   : 涨 {up}天  跌 {down}天  平 {flat}天")
        print("=" * 80)


def main() -> None:
    from astock_analysis.dimensions.kline import fetch_kline

    print()
    print(f"  股票: {STOCK_CODE} (贵州茅台)")
    print(f"  区间: {START_DATE} → {END_DATE}")
    print(f"  周期: daily  |  复权: qfq (前复权)")
    print()

    try:
        response = fetch_kline(STOCK_CODE, START_DATE, END_DATE)
        pprint_kline_response(response)
    except Exception as e:
        print(f"\n  [错误] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
