#!/usr/bin/env python3
"""Generate a comprehensive analysis report for 永鼎股份 (600105)."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["ASTOCK_CONFIG"] = os.path.join(
    os.path.dirname(__file__), "..", "config", "providers.yaml"
)

CODE = "600105"
NAME = "永鼎股份"
INDEX_CODE = "000001"
END_DATE = datetime.now().strftime("%Y-%m-%d")
START_DATE = (datetime.now() - timedelta(30)).strftime("%Y-%m-%d")
START_SHORT = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")


def sep(title: str) -> None:
    print()
    print("=" * 72)
    print(f"  {title}")
    print("=" * 72)


def _parse_amount(v) -> float | None:
    """Parse a value that might be string with Chinese units like '2034.68万'."""
    if v is None or v is False or v == "False":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(v)
    except (ValueError, TypeError):
        pass
    s = str(v).strip()
    if s.endswith("万"):
        try:
            return float(s[:-1]) * 1e4
        except ValueError:
            return None
    if s.endswith("亿"):
        try:
            return float(s[:-1]) * 1e8
        except ValueError:
            return None
    return None


def _parse_pct(v) -> float | None:
    """Parse a percentage value like '38.56%' or 38.56 or '38.56'."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).replace("%", ""))
    except (ValueError, TypeError):
        return None


def _fmt_date(d) -> str:
    """Format a date value to 'YYYY-MM-DD' string."""
    return str(d)[:10]


def main() -> None:
    from astock_analysis.dimensions.kline import fetch_kline
    from astock_analysis.dimensions.realtime import fetch_realtime
    from astock_analysis.dimensions.stock_info import fetch_stock_info
    from astock_analysis.dimensions.financials import fetch_financials
    from astock_analysis.dimensions.holder import fetch_holder
    from astock_analysis.dimensions.capital_flow import fetch_capital_flow
    from astock_analysis.dimensions.index import fetch_index
    from astock_analysis.dimensions.sentiment import fetch_sentiment
    from astock_analysis.dimensions.news import fetch_news
    from astock_analysis.dimensions.industry import fetch_industry
    from astock_analysis.dimensions.concept import fetch_concept
    from astock_analysis.dimensions.margin import fetch_margin
    from astock_analysis.dimensions.lhb import fetch_lhb
    from astock_analysis.dimensions.block_trade import fetch_block_trade
    from astock_analysis.dimensions.north_flow import fetch_north_flow

    now = datetime.now()

    # ══════════════════════════════════════════════════════════════════
    # HEADER
    # ══════════════════════════════════════════════════════════════════
    print("=" * 72)
    print(f"  永鼎股份 (600105)  综合分析报告")
    print(f"  生成时间: {now.strftime('%Y-%m-%d %H:%M')}")
    print(f"  数据范围: {START_DATE} → {END_DATE}")
    print("=" * 72)

    # ══════════════════════════════════════════════════════════════════
    # 1. 基本信息
    # ══════════════════════════════════════════════════════════════════
    sep("一、基本信息")
    try:
        info = fetch_stock_info(CODE)
        print(f"  股票简称:   {info.get('name', 'N/A')}")
        print(f"  公司全称:   {info.get('full_name', 'N/A')}")
        print(f"  所属行业:   {info.get('industry', 'N/A')}")
        print(f"  上市日期:   {info.get('list_date', 'N/A')}")
        print(f"  省份:       {info.get('province', 'N/A')}")
        if info.get("total_shares"):
            print(f"  总股本:     {info['total_shares']:.0f} 股")
        if info.get("circ_shares"):
            print(f"  流通股本:   {info['circ_shares']:.0f} 股")
    except Exception as e:
        print(f"  [获取失败] {e}")

    # ══════════════════════════════════════════════════════════════════
    # 2. 实时行情
    # ══════════════════════════════════════════════════════════════════
    sep("二、实时行情")
    try:
        rt = fetch_realtime(CODE)
        price = rt.get("price", 0)
        change = rt.get("change", 0)
        pct_chg = rt.get("pct_chg", 0)
        direction = "↑" if change > 0 else ("↓" if change < 0 else "—")
        print(f"  最新价:     {price:.2f} 元")
        print(f"  涨跌:       {direction} {change:+.2f}  ({pct_chg:+.2f}%)")
        print(f"  今开:       {rt.get('open', 0):.2f}")
        print(f"  最高:       {rt.get('high', 0):.2f}")
        print(f"  最低:       {rt.get('low', 0):.2f}")
        print(f"  成交量:     {rt.get('volume', 0):.0f} 股")
        print(f"  成交额:     {rt.get('amount', 0):.2f} 元")
        print(f"  换手率:     {rt.get('turnover', 0):.2f}%")
        if rt.get("pe"):
            print(f"  市盈率(动): {rt['pe']:.2f}")
        if rt.get("pb"):
            print(f"  市净率:     {rt['pb']:.2f}")
        if rt.get("total_mv"):
            print(f"  总市值:     {rt['total_mv'] / 1e8:.2f} 亿")
        if rt.get("circ_mv"):
            print(f"  流通市值:   {rt['circ_mv'] / 1e8:.2f} 亿")
    except Exception as e:
        print(f"  [获取失败] {e}")

    # ══════════════════════════════════════════════════════════════════
    # 3. K线走势
    # ══════════════════════════════════════════════════════════════════
    sep("三、近期K线走势 (90日)")
    try:
        kl = fetch_kline(CODE, START_DATE, END_DATE)
        records = kl.get("records", [])
        if records:
            recent = records[-10:]  # Last 10 days
            print(f"  总记录数:   {len(records)} 条")
            print(f"  区间最高:   {max(r['high'] for r in records):.2f}")
            print(f"  区间最低:   {min(r['low'] for r in records):.2f}")
            first_close = records[0]["close"] if records else 0
            last_close = records[-1]["close"] if records else 0
            if first_close:
                period_chg = (last_close - first_close) / first_close * 100
                print(f"  区间涨跌幅: {period_chg:+.2f}%")
            # Volume analysis
            avg_vol = sum(r["volume"] for r in records) / len(records) if records else 0
            print(f"  日均成交量: {avg_vol:.0f} 股")
            first_vol = records[0]["volume"] if records else 0
            last_vol = records[-1]["volume"] if records else 0
            if first_vol:
                vol_chg = (last_vol - first_vol) / first_vol * 100
                print(f"  量比(首尾): {vol_chg:+.1f}%")

            print()
            print(f"  {'日期':<12} {'开盘':>8} {'最高':>8} {'最低':>8} {'收盘':>8} {'涨跌幅':>8} {'成交量':>12}")
            print("  " + "-" * 66)
            for r in recent:
                pct = f"{r['pct_chg']:+.2f}%" if r.get("pct_chg") is not None else "N/A"
                print(
                    f"  {_fmt_date(r['date']):<12} {r['open']:>8.2f} {r['high']:>8.2f} "
                    f"{r['low']:>8.2f} {r['close']:>8.2f} {pct:>8} {r['volume']:>12.0f}"
                )
    except Exception as e:
        print(f"  [获取失败] {e}")

    # ══════════════════════════════════════════════════════════════════
    # 4. 大盘环境
    # ══════════════════════════════════════════════════════════════════
    sep("四、大盘环境")
    try:
        idx = fetch_index(INDEX_CODE, START_SHORT, END_DATE)
        idx_records = idx.get("records", [])
        if idx_records:
            idx_close = idx_records[-1]["close"]
            idx_first = idx_records[0]["close"]
            idx_chg = (idx_close - idx_first) / idx_first * 100
            print(f"  上证指数:   {idx_close:.2f}")
            print(f"  近30日涨跌: {idx_chg:+.2f}%")
    except Exception as e:
        print(f"  [获取失败] {e}")

    try:
        sentiment = fetch_sentiment()
        print(f"  市场情绪:   {sentiment.get('market_sentiment', 'N/A')}")
        print(f"  上涨家数:   {sentiment.get('rise_count', 'N/A')}")
        print(f"  下跌家数:   {sentiment.get('fall_count', 'N/A')}")
        print(f"  涨停家数:   {sentiment.get('limit_up_count', 'N/A')}")
        print(f"  跌停家数:   {sentiment.get('limit_down_count', 'N/A')}")
    except Exception as e:
        print(f"  [获取失败] {e}")

    # ══════════════════════════════════════════════════════════════════
    # 5. 财务数据
    # ══════════════════════════════════════════════════════════════════
    sep("五、财务数据 (近5期)")
    try:
        fin = fetch_financials(CODE)
        records = fin.get("data", [])
        if records:
            recent_fin = records[-5:]
            print(f"  {'报告期':<12} {'净利润(元)':>16} {'同比':>10} {'营收(元)':>16} {'ROE':>8} {'毛利率':>8}")
            print("  " + "-" * 78)
            for r in recent_fin:
                profit = _parse_amount(r.get("net_profit"))
                revenue = _parse_amount(r.get("revenue"))
                yoy = _parse_pct(r.get("net_profit_yoy"))
                roe = _parse_pct(r.get("roe"))
                gm = _parse_pct(r.get("gross_margin"))
                profit_str = f"{profit/1e8:.2f}亿" if profit else "N/A"
                rev_str = f"{revenue/1e8:.2f}亿" if revenue else "N/A"
                yoy_str = f"{yoy:+.2f}%" if yoy is not None else "N/A"
                roe_str = f"{roe:.2f}%" if roe is not None else "N/A"
                gm_str = f"{gm:.2f}%" if gm is not None else "N/A"
                print(
                    f"  {_fmt_date(r.get('report_date', '')):<12} {profit_str:>16} {yoy_str:>10} "
                    f"{rev_str:>16} {roe_str:>8} {gm_str:>8}"
                )
            # Summary
            latest = recent_fin[-1]
            yoy_val = _parse_pct(latest.get("net_profit_yoy"))
            roe_val = _parse_pct(latest.get("roe"))
            gm_val = _parse_pct(latest.get("gross_margin"))
            debt_val = _parse_pct(latest.get("debt_ratio"))
            print()
            if yoy_val is not None:
                yoy_label = "增长" if yoy_val > 0 else "下降"
                print(f"  最新净利润同比: {yoy_label} {yoy_val:+.2f}%")
            if roe_val is not None:
                print(f"  最新ROE:       {roe_val:.2f}%")
            if gm_val is not None:
                print(f"  最新毛利率:    {gm_val:.2f}%")
            if debt_val is not None:
                print(f"  资产负债率:    {debt_val:.2f}%")
    except Exception as e:
        print(f"  [获取失败] {e}")

    # ══════════════════════════════════════════════════════════════════
    # 6. 资金流向
    # ══════════════════════════════════════════════════════════════════
    sep("六、资金流向")
    try:
        cf = fetch_capital_flow(CODE)
        cf_records = cf.get("records", [])
        if cf_records:
            recent_cf = cf_records[-5:]
            print(f"  {'日期':<12} {'主力净流入':>14} {'主力占比':>10} {'超大单净额':>14} {'大单净额':>14}")
            print("  " + "-" * 68)
            for r in recent_cf:
                main_in = r.get("main_net_inflow")
                main_pct = r.get("main_net_pct")
                super_net = r.get("super_large_net")
                large_net = r.get("large_net")
                main_str = f"{main_in/1e4:.0f}万" if main_in else "N/A"
                pct_str = f"{main_pct:+.2f}%" if main_pct is not None else "N/A"
                super_str = f"{super_net/1e4:.0f}万" if super_net else "N/A"
                large_str = f"{large_net/1e4:.0f}万" if large_net else "N/A"
                print(
                    f"  {_fmt_date(r.get('date', '')):<12} {main_str:>14} {pct_str:>10} "
                    f"{super_str:>14} {large_str:>14}"
                )
            # Net flow summary
            total_main = sum(
                r.get("main_net_inflow", 0) or 0 for r in cf_records[-20:]
            )
            direction = "流入" if total_main > 0 else "流出"
            print(f"\n  近20日主力累计: {direction} {abs(total_main)/1e8:.2f}亿")
    except Exception as e:
        print(f"  [获取失败] {e}")

    # ══════════════════════════════════════════════════════════════════
    # 7. 融资融券
    # ══════════════════════════════════════════════════════════════════
    sep("七、融资融券")
    try:
        margin = fetch_margin(CODE, use_cache=False)
        m_data = margin.get("data", [])
        if m_data:
            recent_m = m_data[-5:]
            print(f"  总记录: {len(m_data)} 条")
            for r in recent_m:
                date_val = r.get("信用交易日期", "") or r.get("date", "")
                code_val = r.get("标的证券代码", "") or r.get("code", "")
                name_val = r.get("标的证券简称", "") or r.get("name", "")
                buy = r.get("融资买入额", r.get("margin_buy", "N/A"))
                sell = r.get("融券卖出量", r.get("short_sell", "N/A"))
                bal = r.get("融资余额", r.get("margin_balance", "N/A"))
                print(f"  {_fmt_date(r.get('交易日期', ''))} {name_val}({code_val}) 融资买入:{buy} 融资余额:{bal}")
        else:
            print("  无融资融券记录")
    except Exception as e:
        print(f"  [获取失败] {e}")

    # ══════════════════════════════════════════════════════════════════
    # 8. 股东数据
    # ══════════════════════════════════════════════════════════════════
    sep("八、股东户数变化")
    try:
        holder = fetch_holder(CODE)
        h_records = holder.get("records", [])
        if h_records:
            recent_h = h_records[-5:]
            print(f"  {'截止日期':<12} {'股东户数':>12} {'户均持股':>10} {'户均市值':>12}")
            print("  " + "-" * 52)
            for r in recent_h:
                hc = r.get("holder_count")
                avg_s = r.get("avg_shares")
                avg_v = r.get("avg_value")
                hc_str = f"{hc:.0f}" if hc else "N/A"
                as_str = f"{avg_s:.0f}" if avg_s else "N/A"
                av_str = f"{avg_v/1e4:.1f}万" if avg_v else "N/A"
                print(f"  {_fmt_date(r.get('date', '')):<12} {hc_str:>12} {as_str:>10} {av_str:>12}")
            # Concentration trend
            if len(h_records) >= 2:
                newest = h_records[-1].get("holder_count") or 0
                oldest = h_records[-2].get("holder_count") or 0
                if oldest:
                    h_chg = (newest - oldest) / oldest * 100
                    if h_chg > 3:
                        trend = "分散（户数增加），筹码趋于分散"
                    elif h_chg < -3:
                        trend = "集中（户数减少），筹码趋于集中"
                    else:
                        trend = "基本稳定"
                    print(f"\n  股东户数变化: {h_chg:+.1f}% → 筹码{trend}")
    except Exception as e:
        print(f"  [获取失败] {e}")

    # ══════════════════════════════════════════════════════════════════
    # 9. 大宗交易 & 龙虎榜
    # ══════════════════════════════════════════════════════════════════
    sep("九、大宗交易 & 龙虎榜")
    try:
        bt = fetch_block_trade(CODE, START_DATE, END_DATE)
        bt_data = bt.get("data", [])
        if bt_data:
            print(f"  大宗交易: {len(bt_data)} 笔")
            for r in bt_data[:5]:
                print(f"    {r.get('交易日期', '')}  {r.get('成交价', '')}  {r.get('成交量', '')}股")
        else:
            print(f"  大宗交易: 近90日无记录")
    except Exception as e:
        print(f"  大宗交易: [获取失败] {e}")

    try:
        lhb = fetch_lhb(CODE, START_DATE, END_DATE)
        lhb_data = lhb.get("data", [])
        if lhb_data:
            print(f"  龙虎榜: {len(lhb_data)} 次上榜")
        else:
            print(f"  龙虎榜: 近90日无上榜记录")
    except Exception as e:
        print(f"  龙虎榜: [获取失败] {e}")

    # ══════════════════════════════════════════════════════════════════
    # 10. 相关新闻
    # ══════════════════════════════════════════════════════════════════
    sep("十、相关新闻 (近10条)")
    try:
        news = fetch_news(CODE)
        articles = news.get("records", []) or news.get("data", [])
        if articles:
            for i, a in enumerate(articles[:10], 1):
                title = a.get("新闻标题", "") or a.get("title", "")
                t = a.get("发布时间", "") or a.get("time", "")
                print(f"  {i:>2}. {title}")
                if t:
                    print(f"      发布时间: {t}")
        else:
            print("  无相关新闻")
    except Exception as e:
        print(f"  [获取失败] {e}")

    # ══════════════════════════════════════════════════════════════════
    # 11. 行业板块 & 概念板块
    # ══════════════════════════════════════════════════════════════════
    sep("十一、行业与概念板块 (前10)")
    # Get the stock's industry from stock_info
    stock_industry = ""
    try:
        info2 = fetch_stock_info(CODE)
        stock_industry = str(info2.get("industry", ""))
    except Exception:
        pass

    if stock_industry:
        print(f"  所属行业: {stock_industry}")
        print()

    try:
        ind = fetch_industry()
        ind_data = ind.get("data", [])
        if ind_data:
            print("  行业板块概览:")
            for r in ind_data[:10]:
                name = r.get("name", "") or r.get("板块名称", "")
                code_val = r.get("code", "") or r.get("板块代码", "")
                print(f"    {name} ({code_val})")
    except Exception as e:
        print(f"  [行业板块获取失败] {e}")

    print()
    try:
        con = fetch_concept()
        con_data = con.get("data", [])
        if con_data:
            print("  概念板块概览:")
            for r in con_data[:10]:
                name = r.get("name", "") or r.get("板块名称", "")
                code_val = r.get("code", "") or r.get("板块代码", "")
                print(f"    {name} ({code_val})")
    except Exception as e:
        print(f"  [概念板块获取失败] {e}")

    # ══════════════════════════════════════════════════════════════════
    # 12. 北向资金
    # ══════════════════════════════════════════════════════════════════
    sep("十二、北向资金 (近5日)")
    try:
        nf = fetch_north_flow()
        nf_records = nf.get("data", [])
        if nf_records:
            recent_nf = nf_records[-5:]
            for r in recent_nf:
                date_val = _fmt_date(r.get("日期", ""))
                net = r.get("当日成交净买额")
                buy = r.get("买入成交额")
                sell = r.get("卖出成交额")
                net_str = f"{net:.2f}亿" if net else "N/A"
                buy_str = f"{buy:.2f}亿" if buy else "N/A"
                sell_str = f"{sell:.2f}亿" if sell else "N/A"
                print(f"  {date_val}  净买额: {net_str}  买入: {buy_str}  卖出: {sell_str}")
        else:
            print("  无北向资金数据")
    except Exception as e:
        print(f"  [获取失败] {e}")

    # ══════════════════════════════════════════════════════════════════
    # FOOTER
    # ══════════════════════════════════════════════════════════════════
    sep("免责声明")
    print("  本报告由 astock-analysis 自动生成，数据来源于公开市场信息。")
    print("  仅供参考，不构成任何投资建议。投资有风险，入市需谨慎。")
    print()
    print(f"  数据提供方: akshare / East Money / 同花顺 / 新浪 / 腾讯")
    print(f"  生成时间:   {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 72)


if __name__ == "__main__":
    main()
