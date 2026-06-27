"""Akshare data provider.

Wraps akshare library calls for A-share data. Supports 19 dimensions:
- kline:             Historical OHLCV with forward-adjusted prices
- realtime:          Real-time quote snapshot
- financials:        Financial statements (profit, balance, cash flow)
- capital_flow:      Individual stock fund flow
- lhb:               Dragon-Tiger Board (龙虎榜)
- sentiment:         Market breadth and mood indicators
- index:             Index daily data
- industry:          Industry board data
- concept:           Concept board data
- margin:            Margin trading (融资融券) detail
- block_trade:       Block trade (大宗交易) records
- holder:            Shareholder structure
- north_flow:        Northbound (沪/深港通) capital flow
- news:              Stock-related news
- fund:              ETF/fund data
- stock_info:        Basic stock metadata
- ipo:               IPO/new stock listing data
- futures:           Futures market data
- bond_convertible:  Convertible bond listings

Import is lazy — the module loads even if akshare is not installed,
but methods will raise ProviderError on first call.
"""

from __future__ import annotations

import json
import logging
import re
import time
import urllib.request

import pandas as pd
import requests

from astock_analysis.core.chain import ProviderError

logger = logging.getLogger(__name__)

try:
    import akshare as ak

    _AK_AVAILABLE = True
except ImportError:
    ak = None  # type: ignore[assignment]
    _AK_AVAILABLE = False


class AkshareProvider:
    """Provider wrapping akshare for A-share data.

    Methods follow the naming convention: fetch_{dimension}.
    Each method accepts standard arguments and returns the dimension's
    expected type (see dimensions/{dim}/types.py for TypedDict definitions).

    Methods that raise ProviderError when akshare is not installed or
    the requested data cannot be retrieved.
    """

    name = "akshare"
    requires_key = False
    markets = ("A",)

    @staticmethod
    def _prefix_index_code(code: str) -> str:
        """Add market prefix to index code for akshare APIs.

        Index codes like '000001' (SSE Composite) need 'sh' prefix,
        '399001' (SZSE Component) need 'sz' prefix.
        """
        if code.startswith(("sh", "sz", "csi")):
            return code
        if code.startswith(("000", "510", "511", "600", "601", "603", "605", "688")):
            return f"sh{code}"
        if code.startswith(("002", "300", "301", "399")):
            return f"sz{code}"
        if code.startswith("8"):
            return f"bj{code}"
        return f"sh{code}"

    @staticmethod
    def _eastmoney_json(url: str, params: dict | None = None) -> dict:
        """Call an East Money API endpoint using urllib.

        East Money blocks the Python requests library's TLS fingerprint.
        urllib.request has a different fingerprint that works.
        """
        import urllib.parse

        if params:
            url = url + "?" + urllib.parse.urlencode(params)
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": "*/*",
            "Referer": "https://data.eastmoney.com/",
        }
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw)
        except Exception as e:
            raise ProviderError(f"East Money API request failed: {e}") from e

    @staticmethod
    def _parse_chinese_amount(value: str) -> float:
        """Parse a Chinese-unit amount string like '-7954.17万' to float."""
        raw = str(value).strip()
        if not raw or raw == "nan":
            return 0.0
        try:
            return float(raw)
        except ValueError:
            pass
        if raw.endswith("万"):
            try:
                return float(raw[:-1]) * 1e4
            except ValueError:
                pass
        if raw.endswith("亿"):
            try:
                return float(raw[:-1]) * 1e8
            except ValueError:
                pass
        logger.warning("Could not parse Chinese amount: %r", value)
        return 0.0

    # ── K-line ──────────────────────────────────────────────────

    def fetch_kline(
        self,
        code: str,
        start_date: str,
        end_date: str,
        period: str = "daily",
        adjust: str = "qfq",
    ) -> pd.DataFrame:
        """Fetch historical daily K-line data.

        Args:
            code: A-share stock code (e.g. '600519')
            start_date: Start date in 'YYYYMMDD' or 'YYYY-MM-DD' format
            end_date: End date in 'YYYYMMDD' or 'YYYY-MM-DD' format
            period: Bar period — 'daily', 'weekly', 'monthly'
            adjust: Price adjustment — 'qfq' (forward), 'hfq' (backward), '' (none)

        Returns:
            DataFrame with columns: date, open, high, low, close, volume,
            amount, amplitude, pct_chg, change, turnover, raw_date
        """
        if not _AK_AVAILABLE:
            raise ProviderError(
                "akshare is not installed. Run: pip install akshare"
            )

        # Normalize date format to YYYYMMDD for akshare
        start = start_date.replace("-", "")
        end = end_date.replace("-", "")

        # Try East Money first (primary data source)
        try:
            return self._fetch_kline_eastmoney(code, start, end, period, adjust)
        except Exception:
            logger.warning(
                "East Money kline failed for %s, falling back to Tencent", code
            )
            return self._fetch_kline_tencent(code, start, end, period, adjust)

    def _fetch_kline_eastmoney(
        self, code: str, start: str, end: str, period: str, adjust: str
    ) -> pd.DataFrame:
        """Fetch kline via East Money (akshare stock_zh_a_hist)."""
        try:
            df = ak.stock_zh_a_hist(  # type: ignore[union-attr]
                symbol=code,
                period=period,
                start_date=start,
                end_date=end,
                adjust=adjust,
            )
        except Exception as e:
            raise ProviderError(f"akshare kline fetch failed for {code}: {e}") from e

        if df is None or df.empty:
            raise ProviderError(f"akshare returned empty kline data for {code}")

        return self._standardize_columns(df, source="eastmoney")

    def _fetch_kline_tencent(
        self, code: str, start: str, end: str, period: str, adjust: str
    ) -> pd.DataFrame:
        """Fetch kline via Tencent (proxy.finance.qq.com)."""
        if period not in ("daily", "weekly", "monthly"):
            raise ProviderError(
                f"Tencent kline only supports daily/weekly/monthly, got {period}"
            )

        # Tencent requires exchange prefix
        if code.startswith("6"):
            symbol = f"sh{code}"
        else:
            symbol = f"sz{code}"

        adjust_param = adjust if adjust in ("qfq", "hfq") else ""
        period_map = {"daily": "day", "weekly": "week", "monthly": "month"}
        freq = period_map[period]

        url = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get"

        start_year = int(start[:4])
        end_year = int(end[:4])
        all_rows = []

        for year in range(start_year, end_year + 1):
            params = {
                "_var": f"kline_{freq}{adjust_param}{year}",
                "param": f"{symbol},{freq},{year}-01-01,{year + 1}-12-31,640,{adjust_param}",
                "r": "0.8205512681390605",
            }
            try:
                r = requests.get(url, params=params, timeout=15)
                r.raise_for_status()
            except requests.RequestException as e:
                raise ProviderError(
                    f"Tencent kline HTTP error for {code}: {e}"
                ) from e

            # Parse JSONP response
            text = r.text
            match = re.search(r"=\s*(\{.*\})", text, re.DOTALL)
            if not match:
                raise ProviderError(
                    f"Tencent kline unparseable response for {code}"
                )
            data = json.loads(match.group(1))

            symbol_data = data.get("data", {}).get(symbol)
            if not symbol_data:
                raise ProviderError(
                    f"Tencent kline no data for {code} (symbol {symbol})"
                )

            key = f"{adjust_param}{freq}" if adjust_param else freq
            rows = symbol_data.get(key, [])
            all_rows.extend(rows)

        if not all_rows:
            raise ProviderError(f"Tencent returned empty kline data for {code}")

        # Tencent raw format: [date, open, close, high, low, volume, {}, pct_chg, amount, ""]
        records = []
        for row in all_rows:
            if len(row) < 9:
                continue
            records.append({
                "date": row[0],
                "open": float(row[1]),
                "close": float(row[2]),
                "high": float(row[3]),
                "low": float(row[4]),
                "volume": float(row[5]),
                "pct_chg": float(row[7]) if row[7] else None,
                "amount": float(row[8]) * 10000 if row[8] else 0.0,  # 万元 → 元
            })

        df = pd.DataFrame(records)

        # Filter date range
        start_fmt = f"{start[:4]}-{start[4:6]}-{start[6:8]}"
        end_fmt = f"{end[:4]}-{end[4:6]}-{end[6:8]}"
        df = df[(df["date"] >= start_fmt) & (df["date"] <= end_fmt)]

        if df.empty:
            raise ProviderError(f"Tencent returned empty kline data for {code}")

        logger.info(
            "akshare kline (tencent): %s rows for %s (%s → %s)",
            len(df),
            code,
            start,
            end,
        )
        return df

    def _standardize_columns(
        self, df: pd.DataFrame, source: str
    ) -> pd.DataFrame:
        """Standardize DataFrame columns to the project's expected format."""
        if source == "eastmoney":
            df = df.rename(
                columns={
                    "日期": "date",
                    "开盘": "open",
                    "收盘": "close",
                    "最高": "high",
                    "最低": "low",
                    "成交量": "volume",
                    "成交额": "amount",
                    "振幅": "amplitude",
                    "涨跌幅": "pct_chg",
                    "涨跌额": "change",
                    "换手率": "turnover",
                }
            )

        # Keep only standard columns
        standard_cols = [
            "date",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "amount",
            "pct_chg",
        ]
        extra_cols = [c for c in ["amplitude", "change", "turnover"] if c in df.columns]
        df = df[standard_cols + extra_cols]

        # Ensure numeric types
        for col in ["open", "high", "low", "close", "volume", "amount", "pct_chg"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        return df


    # ── Realtime quote ────────────────────────────────────────────

    def fetch_realtime(self, code: str) -> dict:
        """Fetch real-time quote for a single A-share stock.

        Args:
            code: A-share stock code (e.g. '600519')

        Returns:
            dict with keys: code, name, price, open, high, low, volume,
            amount, change, pct_chg, turnover, pe, pb, total_mv, circ_mv
        """
        if not _AK_AVAILABLE:
            raise ProviderError("akshare is not installed. Run: pip install akshare")

        try:
            return self._fetch_realtime_eastmoney(code)
        except Exception:
            logger.warning(
                "East Money realtime failed for %s, falling back to Tencent", code
            )
            return self._fetch_realtime_tencent(code)

    def _fetch_realtime_eastmoney(self, code: str) -> dict:
        """Fetch realtime via East Money (akshare stock_zh_a_spot_em)."""
        try:
            df = ak.stock_zh_a_spot_em()  # type: ignore[union-attr]
        except Exception as e:
            raise ProviderError(f"East Money realtime fetch failed: {e}") from e

        if df is None or df.empty:
            raise ProviderError("East Money returned empty realtime data")

        row = df[df["代码"] == code]
        if row.empty:
            raise ProviderError(f"Stock code {code} not found in East Money realtime data")

        r = row.iloc[0]
        return {
            "code": code,
            "name": str(r.get("名称", "")),
            "price": float(r.get("最新价", 0)),
            "open": float(r.get("今开", 0)),
            "high": float(r.get("最高", 0)),
            "low": float(r.get("最低", 0)),
            "volume": float(r.get("成交量", 0)),
            "amount": float(r.get("成交额", 0)),
            "change": float(r.get("涨跌额", 0)),
            "pct_chg": float(r.get("涨跌幅", 0)),
            "turnover": float(r.get("换手率", 0)),
            "pe": float(r["市盈率-动态"]) if pd.notna(r.get("市盈率-动态")) else None,
            "pb": float(r["市净率"]) if pd.notna(r.get("市净率")) else None,
            "total_mv": float(r["总市值"]) if pd.notna(r.get("总市值")) else None,
            "circ_mv": float(r["流通市值"]) if pd.notna(r.get("流通市值")) else None,
        }

    def _fetch_realtime_tencent(self, code: str) -> dict:
        """Fetch realtime via Tencent qt.gtimg.cn API."""
        if code.startswith("6"):
            symbol = f"sh{code}"
        else:
            symbol = f"sz{code}"

        url = "https://qt.gtimg.cn/"
        params = {"q": symbol}
        try:
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
        except requests.RequestException as e:
            raise ProviderError(f"Tencent realtime HTTP error for {code}: {e}") from e

        # Parse the JSONP-like response: v_sh600519="field1~field2~...";
        text = r.text
        marker = f'v_{symbol}='
        if marker not in text:
            raise ProviderError(f"Tencent realtime unexpected response format for {code}")
        data_str = text.split(marker)[1].split('";')[0].strip('"')
        fields = data_str.split("~")

        if len(fields) < 47:
            raise ProviderError(f"Tencent realtime insufficient fields ({len(fields)}) for {code}")

        def _f(i: int) -> str:
            return fields[i] if i < len(fields) else ""

        def _float(v: str) -> float | None:
            try:
                return float(v) if v else None
            except ValueError:
                return None

        # Tencent quote field mapping:
        #  3:price  5:open  33:high  34:low  6:volume(lots)
        #  37:amount(wan)  31:change  32:pct_chg  38:turnover
        #  39:PE  46:PB  45:total_mv(yi)  44:circ_mv(yi)
        volume_lots = _float(_f(6))
        amount_wan = _float(_f(37))
        total_mv_yi = _float(_f(45))
        circ_mv_yi = _float(_f(44))

        return {
            "code": code,
            "name": _f(1),
            "price": float(_f(3)),
            "open": float(_f(5)),
            "high": float(_f(33)),
            "low": float(_f(34)),
            "volume": volume_lots * 100 if volume_lots is not None else 0.0,
            "amount": amount_wan * 1e4 if amount_wan is not None else 0.0,
            "change": float(_f(31)),
            "pct_chg": float(_f(32)),
            "turnover": float(_f(38)),
            "pe": _float(_f(39)),
            "pb": _float(_f(46)),
            "total_mv": total_mv_yi * 1e8 if total_mv_yi is not None else None,
            "circ_mv": circ_mv_yi * 1e8 if circ_mv_yi is not None else None,
        }

    # ── Financials ────────────────────────────────────────────────

    def fetch_financials(
        self, code: str, indicator: str = "按报告期"
    ) -> pd.DataFrame:
        """Fetch financial statement data.

        Args:
            code: A-share stock code
            indicator: Report period grouping — '按报告期', '按年度', '按单季度'

        Returns:
            DataFrame with financial indicators per period.
        """
        if not _AK_AVAILABLE:
            raise ProviderError("akshare is not installed. Run: pip install akshare")

        try:
            df = ak.stock_financial_abstract_ths(  # type: ignore[union-attr]
                symbol=code, indicator=indicator
            )
        except Exception as e:
            raise ProviderError(
                f"akshare financials fetch failed for {code}: {e}"
            ) from e

        if df is None or df.empty:
            raise ProviderError(
                f"akshare returned empty financials for {code}"
            )

        # Standardize column names
        col_map = {
            "报告期": "report_date",
            "净利润": "net_profit",
            "净利润同比增长率": "net_profit_yoy",
            "扣非净利润": "deducted_profit",
            "营业总收入": "revenue",
            "营业总收入同比增长率": "revenue_yoy",
            "每股净资产": "bps",
            "净资产收益率": "roe",
            "每股经营现金流": "cfps",
            "销售毛利率": "gross_margin",
            "销售净利率": "net_margin",
            "资产负债率": "debt_ratio",
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
        logger.info(
            "akshare financials: %s rows for %s", len(df), code
        )
        return df

    # ── Capital flow ──────────────────────────────────────────────

    def fetch_capital_flow(self, code: str) -> pd.DataFrame:
        """Fetch individual stock capital flow data.

        Args:
            code: A-share stock code

        Returns:
            DataFrame with daily fund flow details.
        """
        if not _AK_AVAILABLE:
            raise ProviderError("akshare is not installed. Run: pip install akshare")

        market = "sh" if code.startswith("6") else "sz"
        # Tier 1: akshare wrapper (uses requests — blocked by East Money)
        try:
            df = ak.stock_individual_fund_flow(  # type: ignore[union-attr]
                stock=code, market=market
            )
        except Exception as e:
            # Tier 2: urllib direct call (different TLS fingerprint)
            logger.warning(
                "akshare capital_flow failed for %s (%s), falling back to urllib", code, e
            )
            try:
                df = self._fetch_capital_flow_urllib(code, market)
            except Exception as e2:
                # Tier 3: THS snapshot (today's data only, different source)
                logger.warning(
                    "urllib capital_flow failed for %s (%s), falling back to THS", code, e2
                )
                df = self._fetch_capital_flow_ths(code)

        if df is None or df.empty:
            raise ProviderError(
                f"akshare returned empty capital flow for {code}"
            )

        col_map = {
            "日期": "date",
            "主力净流入-净额": "main_net_inflow",
            "主力净流入-净占比": "main_net_pct",
            "超大单净流入-净额": "super_large_net",
            "超大单净流入-净占比": "super_large_pct",
            "大单净流入-净额": "large_net",
            "大单净流入-净占比": "large_pct",
            "中单净流入-净额": "medium_net",
            "中单净流入-净占比": "medium_pct",
            "小单净流入-净额": "small_net",
            "小单净流入-净占比": "small_pct",
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
        logger.info("akshare capital_flow: %s rows for %s", len(df), code)
        return df

    def _fetch_capital_flow_urllib(self, code: str, market: str) -> pd.DataFrame:
        """Fetch capital flow via urllib (bypasses requests TLS fingerprinting)."""
        market_map = {"sh": 1, "sz": 0, "bj": 0}
        url = "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get"
        params = {
            "lmt": "0",
            "klt": "101",
            "secid": f"{market_map.get(market, 0)}.{code}",
            "fields1": "f1,f2,f3,f7",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65",
            "ut": "b2884a393a59ad64002292a3e90d46a5",
            "_": str(int(time.time() * 1000)),
        }
        data = self._eastmoney_json(url, params)
        content_list = data.get("data", {}).get("klines", [])
        if not content_list:
            raise ProviderError(f"urllib capital flow returned empty data for {code}")

        records = [item.split(",") for item in content_list]
        df = pd.DataFrame(records)
        df.columns = [
            "日期",
            "主力净流入-净额",
            "小单净流入-净额",
            "中单净流入-净额",
            "大单净流入-净额",
            "超大单净流入-净额",
            "主力净流入-净占比",
            "小单净流入-净占比",
            "中单净流入-净占比",
            "大单净流入-净占比",
            "超大单净流入-净占比",
            "收盘价",
            "涨跌幅",
            "-",
            "-",
        ]
        return df

    def _fetch_capital_flow_ths(self, code: str) -> pd.DataFrame:
        """Fetch today's capital flow snapshot from THS (同花顺).

        Only provides the current day's aggregate data, not historical.
        Used as a last-resort fallback when East Money is unavailable.
        """
        df = ak.stock_fund_flow_individual(  # type: ignore[union-attr]
            symbol="即时"
        )
        # THS uses int for stock code; normalize to string comparison
        df["_code_str"] = df["股票代码"].astype(str)
        row = df[df["_code_str"] == str(code)]
        if row.empty:
            raise ProviderError(
                f"THS capital flow: stock {code} not found in today's flow data"
            )
        r = row.iloc[0]
        import datetime

        # Parse net flow value which may be in Chinese units (万 = 1e4, 亿 = 1e8)
        raw_net = str(r.get("净额", 0))
        net_value = self._parse_chinese_amount(raw_net)
        today = datetime.date.today().isoformat()
        return pd.DataFrame([{
            "日期": today,
            "主力净流入-净额": net_value,
            "主力净流入-净占比": None,
            "超大单净流入-净额": None,
            "超大单净流入-净占比": None,
            "大单净流入-净额": None,
            "大单净流入-净占比": None,
            "中单净流入-净额": None,
            "中单净流入-净占比": None,
            "小单净流入-净额": None,
            "小单净流入-净占比": None,
        }])

    # ── LHB (龙虎榜) ───────────────────────────────────────────────

    def fetch_lhb(
        self, code: str = "", start_date: str = "", end_date: str = ""
    ) -> pd.DataFrame:
        """Fetch Dragon-Tiger Board (龙虎榜) data.

        Args:
            code: Optional stock code filter
            start_date: Start date 'YYYYMMDD' or 'YYYY-MM-DD'
            end_date: End date 'YYYYMMDD' or 'YYYY-MM-DD'

        Returns:
            DataFrame with LHB detail records.
        """
        if not _AK_AVAILABLE:
            raise ProviderError("akshare is not installed. Run: pip install akshare")

        start = start_date.replace("-", "") if start_date else ""
        end = end_date.replace("-", "") if end_date else ""

        try:
            if start and end:
                df = ak.stock_lhb_detail_em(  # type: ignore[union-attr]
                    start_date=start, end_date=end
                )
            else:
                df = ak.stock_lhb_detail_em()  # type: ignore[union-attr]
        except Exception as e:
            raise ProviderError(f"akshare LHB fetch failed: {e}") from e

        if df is None or df.empty:
            raise ProviderError("akshare returned empty LHB data")

        if code:
            df = df[df["代码"] == code]
            if df.empty:
                logger.info("akshare lhb: no records for %s", code)
                return pd.DataFrame()

        logger.info("akshare lhb: %s rows", len(df))
        return df

    # ── Sentiment ─────────────────────────────────────────────────

    def fetch_sentiment(self) -> dict:
        """Fetch market sentiment indicators.

        Returns:
            dict with: limit_up_count, limit_down_count, rise_count,
            fall_count, flat_count, market_sentiment
        """
        if not _AK_AVAILABLE:
            raise ProviderError("akshare is not installed. Run: pip install akshare")

        try:
            df = ak.stock_zh_a_spot_em()  # type: ignore[union-attr]
        except Exception:
            logger.warning("East Money sentiment failed, falling back to Sina")
            try:
                df = ak.stock_zh_a_spot()  # type: ignore[union-attr]
            except Exception as e2:
                raise ProviderError(
                    f"akshare sentiment fetch failed: {e2}"
                ) from e2

        if df is None or df.empty:
            raise ProviderError("akshare returned empty sentiment data")

        # Normalize column names: Sina uses different names than East Money
        pct_col = "涨跌幅" if "涨跌幅" in df.columns else "changepercent"
        if pct_col not in df.columns:
            raise ProviderError(f"Sentiment data missing price-change column, got: {list(df.columns)[:10]}")
        pct = pd.to_numeric(df[pct_col], errors="coerce")
        rise = int((pct > 0).sum())
        fall = int((pct < 0).sum())
        flat = int((pct == 0).sum())
        total = len(df)

        # Rough limit-up/down detection (>= 9.5% or <= -9.5% for main board)
        limit_up = int((pct >= 9.5).sum())
        limit_down = int((pct <= -9.5).sum())

        if rise > fall:
            mood = "bullish"
        elif fall > rise:
            mood = "bearish"
        else:
            mood = "neutral"

        logger.info(
            "akshare sentiment: rise=%s fall=%s limit_up=%s limit_down=%s",
            rise, fall, limit_up, limit_down,
        )
        return {
            "total": total,
            "rise_count": rise,
            "fall_count": fall,
            "flat_count": flat,
            "limit_up_count": limit_up,
            "limit_down_count": limit_down,
            "market_sentiment": mood,
        }

    # ── Index ─────────────────────────────────────────────────────

    def fetch_index(
        self, code: str, start_date: str = "", end_date: str = ""
    ) -> pd.DataFrame:
        """Fetch index daily K-line data.

        Args:
            code: Index code (e.g. '000001' for SSE Composite, '399001' for SZSE Component)
            start_date: Start date 'YYYY-MM-DD', defaults to 60 days ago
            end_date: End date 'YYYY-MM-DD', defaults to today

        Returns:
            DataFrame with daily index OHLCV data.
        """
        if not _AK_AVAILABLE:
            raise ProviderError("akshare is not installed. Run: pip install akshare")

        from datetime import datetime, timedelta

        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")

        symbol = self._prefix_index_code(code)
        try:
            df = ak.stock_zh_index_daily_em(  # type: ignore[union-attr]
                symbol=symbol,
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", ""),
            )
        except Exception:
            logger.warning("East Money index failed for %s, falling back to Tencent", code)
            try:
                df = ak.stock_zh_index_daily_tx(  # type: ignore[union-attr]
                    symbol=symbol,
                    start_date=start_date.replace("-", ""),
                    end_date=end_date.replace("-", ""),
                )
            except Exception as e2:
                raise ProviderError(
                    f"akshare index fetch failed for {code}: {e2}"
                ) from e2

        if df is None or df.empty:
            raise ProviderError(f"akshare returned empty index data for {code}")

        col_map = {
            "date": "date",
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume",
            "amount": "amount",
        }
        existing = {k: v for k, v in col_map.items() if k in df.columns}
        df = df.rename(columns=existing)
        for col in ("volume", "amount"):
            if col not in df.columns:
                df[col] = 0.0
        logger.info("akshare index: %s rows for %s", len(df), code)
        return df

    # ── Industry board ────────────────────────────────────────────

    def fetch_industry(self, board_name: str = "") -> pd.DataFrame:
        """Fetch industry board data.

        Args:
            board_name: Optional industry board name filter.
                        If empty, returns all industry boards.

        Returns:
            DataFrame with industry board information.
        """
        if not _AK_AVAILABLE:
            raise ProviderError("akshare is not installed. Run: pip install akshare")

        try:
            if board_name:
                df = ak.stock_board_industry_hist_em(  # type: ignore[union-attr]
                    symbol=board_name,
                    period="daily",
                    adjust="",
                )
            else:
                # Prefer THS (同花顺) over East Money for listing
                try:
                    df = ak.stock_board_industry_name_em()  # type: ignore[union-attr]
                except Exception:
                    logger.warning("East Money industry failed, falling back to THS")
                    df = ak.stock_board_industry_name_ths()  # type: ignore[union-attr]
        except Exception as e:
            raise ProviderError(f"akshare industry fetch failed: {e}") from e

        if df is None or df.empty:
            raise ProviderError("akshare returned empty industry data")

        logger.info("akshare industry: %s rows", len(df))
        return df

    # ── Concept board ─────────────────────────────────────────────

    def fetch_concept(self, board_name: str = "") -> pd.DataFrame:
        """Fetch concept board data.

        Args:
            board_name: Optional concept board name filter.
                        If empty, returns all concept boards.

        Returns:
            DataFrame with concept board information.
        """
        if not _AK_AVAILABLE:
            raise ProviderError("akshare is not installed. Run: pip install akshare")

        try:
            if board_name:
                df = ak.stock_board_concept_hist_em(  # type: ignore[union-attr]
                    symbol=board_name,
                    period="daily",
                    adjust="",
                )
            else:
                # Prefer East Money, fall back to THS (同花顺)
                try:
                    df = ak.stock_board_concept_name_em()  # type: ignore[union-attr]
                except Exception:
                    logger.warning("East Money concept failed, falling back to THS")
                    df = ak.stock_board_concept_name_ths()  # type: ignore[union-attr]
        except Exception as e:
            raise ProviderError(f"akshare concept fetch failed: {e}") from e

        if df is None or df.empty:
            raise ProviderError("akshare returned empty concept data")

        logger.info("akshare concept: %s rows", len(df))
        return df

    # ── Margin trading ────────────────────────────────────────────

    def fetch_margin(self, code: str = "") -> pd.DataFrame:
        """Fetch margin trading (融资融券) detail data.

        Args:
            code: Optional stock code filter

        Returns:
            DataFrame with margin trading details.
        """
        if not _AK_AVAILABLE:
            raise ProviderError("akshare is not installed. Run: pip install akshare")

        try:
            dfs = []
            for market, fetcher in [
                ("sh", ak.stock_margin_detail_sse),
                ("sz", ak.stock_margin_detail_szse),
            ]:
                try:
                    mkt_df = fetcher(date="")  # type: ignore[union-attr]
                    if mkt_df is not None and not mkt_df.empty:
                        mkt_df["market"] = market
                        dfs.append(mkt_df)
                except Exception:
                    pass

            if not dfs:
                raise ProviderError("akshare margin fetch returned no data")

            df = pd.concat(dfs, ignore_index=True)
        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError(f"akshare margin fetch failed: {e}") from e

        if code:
            df = df[df["标的证券代码"].astype(str) == str(code)] if "标的证券代码" in df.columns else df
            if df.empty:
                raise ProviderError(f"No margin records for {code}")

        logger.info("akshare margin: %s rows", len(df))
        return df

    # ── Block trade (大宗交易) ─────────────────────────────────────

    def fetch_block_trade(
        self, code: str = "", start_date: str = "", end_date: str = ""
    ) -> pd.DataFrame:
        """Fetch block trade (大宗交易) data.

        Args:
            code: Optional stock code filter
            start_date: Start date 'YYYY-MM-DD'
            end_date: End date 'YYYY-MM-DD'

        Returns:
            DataFrame with block trade records.
        """
        if not _AK_AVAILABLE:
            raise ProviderError("akshare is not installed. Run: pip install akshare")

        from datetime import datetime, timedelta

        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        try:
            # stock_dzjy_mrmx expects category ('A股','B股','基金','债券'), not stock code
            df = ak.stock_dzjy_mrmx(  # type: ignore[union-attr]
                symbol="A股",
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", ""),
            )
        except Exception as e:
            raise ProviderError(
                f"akshare block_trade fetch failed: {e}"
            ) from e

        if df is None or df.empty:
            raise ProviderError("akshare returned empty block trade data")

        if code:
            if "证券代码" in df.columns:
                df = df[df["证券代码"].astype(str) == str(code)]
            if df.empty:
                logger.info("akshare block_trade: no records for %s", code)
                return pd.DataFrame()

        logger.info("akshare block_trade: %s rows", len(df))
        return df

    # ── Holder (股东数据) ──────────────────────────────────────────

    def fetch_holder(self, code: str) -> pd.DataFrame:
        """Fetch shareholder structure data.

        Args:
            code: A-share stock code

        Returns:
            DataFrame with top shareholders.
        """
        if not _AK_AVAILABLE:
            raise ProviderError("akshare is not installed. Run: pip install akshare")

        try:
            df = ak.stock_zh_a_gdhs_detail_em(  # type: ignore[union-attr]
                symbol=code
            )
        except Exception as e:
            raise ProviderError(
                f"akshare holder fetch failed for {code}: {e}"
            ) from e

        if df is None or df.empty:
            raise ProviderError(f"akshare returned empty holder data for {code}")

        col_map = {
            "股东户数统计截止日": "date",
            "股东户数-本次": "holder_count",
            "户均持股数量": "avg_shares",
            "户均持股市值": "avg_value",
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
        logger.info("akshare holder: %s rows for %s", len(df), code)
        return df

    # ── Northbound flow (北向资金) ─────────────────────────────────

    def fetch_north_flow(self, code: str = "") -> pd.DataFrame:
        """Fetch northbound (沪/深港通) capital flow data.

        Args:
            code: Optional stock code for individual stock northbound flow.
                  If empty, returns market-level northbound flow.

        Returns:
            DataFrame with northbound flow records.
        """
        if not _AK_AVAILABLE:
            raise ProviderError("akshare is not installed. Run: pip install akshare")

        try:
            df = ak.stock_hsgt_hist_em(  # type: ignore[union-attr]
                symbol=code if code else "沪股通"
            )
        except Exception as e:
            raise ProviderError(
                f"akshare north_flow fetch failed: {e}"
            ) from e

        if df is None or df.empty:
            raise ProviderError("akshare returned empty northbound flow data")

        logger.info("akshare north_flow: %s rows", len(df))
        return df

    # ── News ──────────────────────────────────────────────────────

    def fetch_news(self, code: str = "") -> pd.DataFrame:
        """Fetch stock-related news.

        Args:
            code: A-share stock code

        Returns:
            DataFrame with news articles.
        """
        if not _AK_AVAILABLE:
            raise ProviderError("akshare is not installed. Run: pip install akshare")

        try:
            df = ak.stock_news_em(  # type: ignore[union-attr]
                symbol=code
            )
        except Exception as e:
            raise ProviderError(
                f"akshare news fetch failed for {code}: {e}"
            ) from e

        if df is None or df.empty:
            raise ProviderError(f"akshare returned empty news for {code}")

        logger.info("akshare news: %s rows for %s", len(df), code)
        return df

    # ── Fund ──────────────────────────────────────────────────────

    def fetch_fund(self, code: str = "") -> pd.DataFrame:
        """Fetch ETF/fund data.

        Args:
            code: Optional fund code

        Returns:
            DataFrame with fund information.
        """
        if not _AK_AVAILABLE:
            raise ProviderError("akshare is not installed. Run: pip install akshare")

        try:
            if code:
                df = ak.fund_etf_fund_info_em(  # type: ignore[union-attr]
                    symbol=code
                )
            else:
                df = ak.fund_etf_category_sina(  # type: ignore[union-attr]
                    symbol="ETF基金"
                )
        except Exception as e:
            raise ProviderError(
                f"akshare fund fetch failed: {e}"
            ) from e

        if df is None or df.empty:
            raise ProviderError("akshare returned empty fund data")

        logger.info("akshare fund: %s rows", len(df))
        return df

    # ── Stock info ────────────────────────────────────────────────

    def fetch_stock_info(self, code: str) -> dict:
        """Fetch basic stock information.

        Args:
            code: A-share stock code

        Returns:
            dict with stock metadata.
        """
        # Try East Money API directly (akshare wrapper is version-fragile)
        try:
            return self._fetch_stock_info_eastmoney(code)
        except Exception as e:
            logger.warning(
                "East Money stock_info failed for %s (%s), falling back to CNInfo",
                code, e,
            )
            return self._fetch_stock_info_cninfo(code)

    def _fetch_stock_info_eastmoney(self, code: str) -> dict:
        """Fetch stock info via East Money push2 API (direct call)."""
        market_code = 1 if code.startswith("6") else 0
        url = "https://push2.eastmoney.com/api/qt/stock/get"
        params = {
            "fltt": "2",
            "invt": "2",
            "fields": (
                "f43,f44,f45,f46,f57,f58,f60,f84,f85,f92,f116,f117,"
                "f127,f128,f162,f167,f168,f170,f173,f189"
            ),
            "secid": f"{market_code}.{code}",
        }
        data = self._eastmoney_json(url, params)
        d = data.get("data", {})
        if not d or not d.get("f57"):
            raise ProviderError(
                f"East Money returned empty stock info for {code}"
            )

        raw_name = str(d.get("f58", ""))
        # Remove XD/XR/DR prefix from stock name
        name = raw_name
        for prefix in ("XD", "XR", "DR"):
            if name.startswith(prefix):
                name = name[len(prefix):]
                break

        def _f(field: str) -> float | None:
            val = d.get(field)
            if val is None or val == "-":
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                return None

        return {
            "code": code,
            "name": name,
            "full_name": "",  # full name not available from this endpoint
            "industry": str(d.get("f127", "")),
            "list_date": str(d.get("f189", "")),
            "total_shares": _f("f84"),
            "circ_shares": _f("f85"),
            "province": str(d.get("f128", "")),
            "total_market_cap": _f("f116"),
            "circ_market_cap": _f("f117"),
            "pe": _f("f162"),
            "pb": _f("f167"),
            "eps": _f("f92"),
            "bvps": _f("f173"),
            "price": _f("f43"),
            "turnover": _f("f168"),
            "pct_chg": _f("f170"),
        }

    def _fetch_stock_info_cninfo(self, code: str) -> dict:
        """Fetch stock info via CNInfo fallback."""
        if not _AK_AVAILABLE:
            raise ProviderError("akshare is not installed. Run: pip install akshare")
        try:
            df = ak.stock_profile_cninfo(symbol=code)  # type: ignore[union-attr]
        except Exception as e:
            raise ProviderError(
                f"akshare stock_info (CNInfo) fetch failed for {code}: {e}"
            ) from e
        if df is None or df.empty:
            raise ProviderError(f"akshare returned empty stock info for {code}")
        row = df.iloc[0].to_dict()
        return {
            "code": code,
            "name": str(row.get("A股简称", "")),
            "full_name": str(row.get("公司名称", "")),
            "industry": str(row.get("所属行业", "")),
            "list_date": str(row.get("上市日期", "")),
            "total_shares": None,
            "circ_shares": None,
            "province": str(row.get("注册地址", "")),
            "total_market_cap": None,
            "circ_market_cap": None,
            "pe": None,
            "pb": None,
            "eps": None,
            "bvps": None,
            "price": None,
            "turnover": None,
            "pct_chg": None,
        }

    # ── IPO ───────────────────────────────────────────────────────

    def fetch_ipo(self) -> pd.DataFrame:
        """Fetch IPO/new stock listing data.

        Returns:
            DataFrame with IPO benefit/comparison data.
        """
        if not _AK_AVAILABLE:
            raise ProviderError("akshare is not installed. Run: pip install akshare")

        try:
            df = ak.stock_ipo_ths(  # type: ignore[union-attr]
                symbol="全部A股"
            )
        except Exception as e:
            raise ProviderError(f"akshare ipo fetch failed: {e}") from e

        if df is None or df.empty:
            raise ProviderError("akshare returned empty IPO data")

        logger.info("akshare ipo: %s rows", len(df))
        return df

    # ── Futures ───────────────────────────────────────────────────

    def fetch_futures(self, code: str = "") -> pd.DataFrame:
        """Fetch futures market data.

        Args:
            code: Optional futures contract code

        Returns:
            DataFrame with futures daily data.
        """
        if not _AK_AVAILABLE:
            raise ProviderError("akshare is not installed. Run: pip install akshare")

        try:
            if code:
                df = ak.futures_zh_daily_sina(  # type: ignore[union-attr]
                    symbol=code
                )
            else:
                df = ak.futures_zh_daily_sina(  # type: ignore[union-attr]
                    symbol="IF0"
                )
        except Exception as e:
            raise ProviderError(
                f"akshare futures fetch failed: {e}"
            ) from e

        if df is None or df.empty:
            raise ProviderError("akshare returned empty futures data")

        logger.info("akshare futures: %s rows", len(df))
        return df

    # ── Convertible bond ──────────────────────────────────────────

    def fetch_bond_convertible(self) -> pd.DataFrame:
        """Fetch convertible bond market data.

        Returns:
            DataFrame with convertible bond listings.
        """
        if not _AK_AVAILABLE:
            raise ProviderError("akshare is not installed. Run: pip install akshare")

        try:
            df = ak.bond_cb_jsl(  # type: ignore[union-attr]
                cookie=""
            )
        except Exception as e:
            raise ProviderError(
                f"akshare bond_convertible fetch failed: {e}"
            ) from e

        if df is None or df.empty:
            raise ProviderError("akshare returned empty convertible bond data")

        logger.info("akshare bond_convertible: %s rows", len(df))
        return df


# Create singleton instance for registration
provider = AkshareProvider()
