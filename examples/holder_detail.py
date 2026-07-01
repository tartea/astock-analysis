#!/usr/bin/env python3
"""Holder 股东数据接口详细输出示例。

单独演示 fetch_holder 的调用方式，将返回的完整内容
以表格形式输出到终端。

Usage:
    cd astock-analysis
    pip install -e ".[dev]"
    python examples/holder_detail.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["ASTOCK_CONFIG"] = os.path.join(
    os.path.dirname(__file__), "..", "config", "providers.yaml"
)

STOCK_CODE = "600519"


def pprint_holder(response: dict) -> None:
    """Pretty-print HolderResponse."""
    records = response.get("records", [])

    print("=" * 80)
    print("  HolderResponse 元信息")
    print("=" * 80)
    print(f"  provider     : {response.get('provider', '?')}")
    print(f"  code         : {response.get('code', '?')}")
    print(f"  records      : {len(records)} 条")
    print()

    print("-" * 80)
    print(f"  {'date':<16} {'holder_count':>16} {'avg_shares':>16} {'avg_value':>16}")
    print(f"  {'统计截止日':<16} {'股东户数':>16} {'户均持股':>16} {'户均市值':>16}")
    print("-" * 80)

    for r in records:
        hc = f"{r['holder_count']:>14.0f}" if r.get("holder_count") is not None else "N/A".rjust(16)
        a_s = f"{r['avg_shares']:>14.2f}" if r.get("avg_shares") is not None else "N/A".rjust(16)
        a_v = f"{r['avg_value']:>14.2f}" if r.get("avg_value") is not None else "N/A".rjust(16)
        print(f"  {r['date']:<16} {hc:>16} {a_s:>16} {a_v:>16}")

    print("=" * 80)


def _fmt_num(v: float | None) -> str:
    if v is None:
        return "N/A".rjust(16)
    if abs(v) >= 1e8:
        return f"{v / 1e8:>12.2f}亿"
    if abs(v) >= 1e4:
        return f"{v / 1e4:>12.2f}万"
    return f"{v:>14.0f}"


def _fmt_pct(v: float | None) -> str:
    if v is None:
        return "N/A".rjust(10)
    return f"{v:>8.2f}%"


def pprint_top_holders(response: dict) -> None:
    """Pretty-print TopHolderResponse, grouped by report_date."""
    records = response.get("records", [])
    is_free = response.get("holder_type") == "free_top10"
    label = "十大流通股东" if is_free else "十大股东"
    ratio_label = "占流通股比例" if is_free else "占总股本比例"
    scope_desc = (
        "统计口径: 仅流通股本，含股东性质分类"
        if is_free
        else "统计口径: 总股本（含限售股），无股东性质分类"
    )

    # Group by report_date
    from itertools import groupby
    key = lambda r: r.get("report_date", "")
    grouped = {k: list(g) for k, g in groupby(sorted(records, key=key, reverse=True), key=key)}

    print()
    print("=" * 100)
    print(f"  {label}明细  ({response.get('provider', '?')} | {response.get('code', '?')})")
    print(f"  {scope_desc}")
    print(f"  共 {len(grouped)} 期，{len(records)} 条记录")
    print("=" * 100)

    header = f"  {'排名':<6} {'股东名称':<30} {'类型':<10} {'持股数':>16} {'持股比例':>12} {'增减':>16} {'变动比率':>10}"
    sub_header = f"  {'':6} {'':30} {'':10} {'':16} {ratio_label:>12} {'':16} {'':10}"

    for report_date, items in grouped.items():
        print()
        print(f"  ── 报告期: {report_date} ──")
        print(header)
        print(sub_header)
        print("-" * 100)

        for r in items:
            name = r["holder_name"][:28] if len(r["holder_name"]) > 28 else r["holder_name"]
            nature = (r.get("holder_nature") or "")[:8]
            print(
                f"  #{r['rank']:<4} {name:<30} {nature:<10} "
                f"{_fmt_num(r['share_num']):>16} {_fmt_pct(r['share_ratio']):>12} "
                f"{r.get('share_change', ''):>16} {_fmt_pct(r.get('change_ratio')):>10}"
            )

    print()
    print("=" * 100)


def main() -> None:
    from market_data.dimensions.holder import fetch_holder, fetch_top_holders

    print()
    print(f"  股票: {STOCK_CODE} (贵州茅台)")
    print()

    # ── 股东户数统计 ──
    try:
        response = fetch_holder(STOCK_CODE)
        pprint_holder(response)
    except Exception as e:
        print(f"\n  [错误] 股东户数: {e}")

    # ── 十大流通股东 ──
    try:
        free_top = fetch_top_holders(STOCK_CODE, free=True)
        pprint_top_holders(free_top)
    except Exception as e:
        print(f"\n  [错误] 十大流通股东: {e}")

    # ── 十大股东 ──
    try:
        top10 = fetch_top_holders(STOCK_CODE, free=False)
        pprint_top_holders(top10)
    except Exception as e:
        print(f"\n  [错误] 十大股东: {e}")


if __name__ == "__main__":
    main()
