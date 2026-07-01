#!/usr/bin/env python3
"""North flow 北向资金接口详细输出示例。

单独演示 fetch_north_flow 的调用方式，将返回的完整内容
以表格形式输出到终端。

Usage:
    cd astock-analysis
    pip install -e ".[dev]"
    python examples/north_flow_detail.py              # 市场级
    python examples/north_flow_detail.py 600519.SH    # 个股北向
"""

from __future__ import annotations

import os
import sys
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["ASTOCK_CONFIG"] = os.path.join(
    os.path.dirname(__file__), "..", "config", "providers.yaml"
)


def pprint_north_flow(response: dict) -> None:
    """Pretty-print NorthFlowResponse."""
    data = response.get("data", [])

    print("=" * 120)
    print("  NorthFlowResponse 元信息")
    print("=" * 120)
    print(f"  provider : {response.get('provider', '?')}")
    print(f"  code     : {response.get('code', '?')}")
    print(f"  records  : {len(data)} 条")
    print()

    if not data:
        print("  (无数据)")
        print("=" * 120)
        return

    keys = list(data[0].keys())
    col_widths = {k: max(len(str(k)), 12) for k in keys}
    for row in data:
        for k in keys:
            v = str(row.get(k, ""))
            col_widths[k] = max(col_widths.get(k, 12), len(v))

    header = "  " + "  ".join(f"{k:>{col_widths[k]}}" for k in keys)
    sep = "  " + "  ".join("-" * col_widths[k] for k in keys)

    print(sep)
    print(header)
    print(sep)
    for row in data:
        line = "  " + "  ".join(
            f"{str(row.get(k, '')):>{col_widths[k]}}" for k in keys
        )
        print(line)
    print(sep)
    print("=" * 120)


def main() -> None:
    from market_data.dimensions.north_flow import fetch_north_flow

    code = '60010'
    label = f"个股 {code}" if code else "市场级"

    print()
    print(f"  北向资金 (沪/深港通) {label}数据", end="")
    if code:
        print(" (最近3年)")
    else:
        print(" (最近4个月)")
    print()

    # 市场级数据源持续更新，只取最近4个月；个股数据源较旧，放宽到3年
    days = 1095 if code else 120
    cutoff = date.today() - timedelta(days=days)

    try:
        response = fetch_north_flow(code=code)
        # 只保留最近四个月的数据
        filtered_data = []
        for row in response.get("data", []):
            # 市场级用"日期"，个股用"持股日期"
            date_val = row.get("日期") or row.get("持股日期")
            if isinstance(date_val, date):
                row_date = date_val
            elif isinstance(date_val, str):
                try:
                    row_date = datetime.strptime(date_val[:10], "%Y-%m-%d").date()
                except ValueError:
                    continue
            else:
                continue
            if row_date >= cutoff:
                filtered_data.append(row)
        response["data"] = filtered_data
        pprint_north_flow(response)
    except Exception as e:
        print(f"\n  [错误] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
