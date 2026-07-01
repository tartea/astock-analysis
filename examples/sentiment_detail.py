#!/usr/bin/env python3
"""Sentiment 市场情绪接口详细输出示例。

单独演示 fetch_sentiment 的调用方式，将返回的完整内容
以 key-value 形式输出。

Usage:
    cd astock-analysis
    pip install -e ".[dev]"
    python examples/sentiment_detail.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["ASTOCK_CONFIG"] = os.path.join(
    os.path.dirname(__file__), "..", "config", "providers.yaml"
)


def pprint_sentiment(response: dict) -> None:
    """Pretty-print SentimentResponse."""
    print("=" * 60)
    print("  SentimentResponse - 市场情绪")
    print("=" * 60)

    mood_icon = {"bullish": "看涨 🐂", "bearish": "看跌 🐻", "neutral": "中性"}
    mood = response.get("market_sentiment", "")
    print(f"  市场情绪   : {mood}  ({mood_icon.get(mood, '')})")
    print(f"  总样本     : {response.get('total', 0)}")
    print(f"  上涨家数   : {response.get('rise_count', 0)}")
    print(f"  下跌家数   : {response.get('fall_count', 0)}")
    print(f"  平盘家数   : {response.get('flat_count', 0)}")
    print(f"  涨停家数   : {response.get('limit_up_count', 0)}")
    print(f"  跌停家数   : {response.get('limit_down_count', 0)}")
    print(f"  数据源     : {response.get('provider', '')}")

    total = response.get("rise_count", 0) + response.get("fall_count", 0) + response.get("flat_count", 0)
    if total:
        rise_ratio = response.get("rise_count", 0) / total * 100
        print(f"  上涨比率   : {rise_ratio:.1f}%")
    print("=" * 60)


def main() -> None:
    from market_data.dimensions.sentiment import fetch_sentiment

    print()

    try:
        response = fetch_sentiment()
        pprint_sentiment(response)
    except Exception as e:
        print(f"\n  [错误] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
