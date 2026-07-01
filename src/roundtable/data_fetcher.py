"""数据预取与格式化 —— 动态 import market_data.dimensions，独立实现"""

import inspect
import sys
from datetime import datetime, timedelta
from importlib import import_module

import pandas as pd


# ── 格式化工具 ─────────────────────────────────────────────────

def _df_to_markdown(df: pd.DataFrame, max_rows: int = 20) -> str:
    if df is None or df.empty:
        return "（无数据）"

    if len(df) > max_rows:
        df = df.head(max_rows)

    lines: list[str] = []
    lines.append("| " + " | ".join(str(c) for c in df.columns) + " |")
    lines.append("|" + "|".join("---" for _ in df.columns) + "|")
    for _, row in df.iterrows():
        cells = [str(v)[:60] if pd.notna(v) and str(v) != "nan" else "-" for v in row]
        lines.append("| " + " | ".join(cells) + " |")

    if len(df) > max_rows:
        lines.append(f"\n*（原始数据共 {len(df)} 行，此处仅展示前 {max_rows} 行）*")

    return "\n".join(lines)


def _format_response(data, max_rows: int = 20) -> str:
    if data is None:
        return "（无数据）"

    if isinstance(data, pd.DataFrame):
        return _df_to_markdown(data, max_rows)

    if isinstance(data, dict):
        parts: list[str] = []
        for key, value in data.items():
            if isinstance(value, pd.DataFrame):
                parts.append(f"### {key}\n{_df_to_markdown(value, max_rows)}")
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                for item in value[:max_rows]:
                    parts.append("- " + ", ".join(f"{k}={v}" for k, v in item.items()))
            elif value is not None:
                parts.append(f"- **{key}**: {value}")
        return "\n".join(parts) if parts else "（无数据）"

    if isinstance(data, list):
        lines = [f"- {item}" for item in data[:max_rows]]
        return "\n".join(lines) if lines else "（无数据）"

    return str(data)[:2000]


# ── 维度获取 ───────────────────────────────────────────────────

_FETCH_FUNCTION_CACHE: dict[str, callable] = {}


def _get_fetch_function(dimension: str):
    if dimension in _FETCH_FUNCTION_CACHE:
        return _FETCH_FUNCTION_CACHE[dimension]

    try:
        mod = import_module(f"market_data.dimensions.{dimension}")
        func_name = f"fetch_{dimension}"
        func = getattr(mod, func_name, None)
        if func:
            _FETCH_FUNCTION_CACHE[dimension] = func
            return func
    except ImportError as e:
        print(f"[警告] 无法导入维度模块 {dimension}: {e}", file=sys.stderr)
    except Exception as e:
        print(f"[警告] 导入维度 {dimension} 时出错: {e}", file=sys.stderr)

    _FETCH_FUNCTION_CACHE[dimension] = None
    return None


def _build_kwargs(fetch_func, stock_code: str) -> dict:
    sig = inspect.signature(fetch_func)
    param_names = set(sig.parameters.keys())

    kwargs: dict = {}

    if "code" in param_names:
        kwargs["code"] = stock_code
    elif "ticker" in param_names:
        kwargs["ticker"] = stock_code
    elif "symbol" in param_names:
        kwargs["symbol"] = stock_code

    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if "start_date" in param_names:
        kwargs["start_date"] = start
    if "end_date" in param_names:
        kwargs["end_date"] = end

    if "use_cache" in param_names:
        kwargs["use_cache"] = True

    return kwargs


def _count_rows(data) -> str:
    if data is None:
        return "0 行"
    if isinstance(data, pd.DataFrame):
        return f"{len(data)} 行"
    if isinstance(data, dict):
        parts = []
        for k, v in data.items():
            if isinstance(v, pd.DataFrame):
                parts.append(f"{len(v)} 行")
            elif isinstance(v, list):
                parts.append(f"{len(v)} 条")
            elif v is not None and k != "provider":
                parts.append(f"{k}={v}")
        return ", ".join(parts) if parts else "ok"
    if isinstance(data, list):
        return f"{len(data)} 条"
    return "ok"


async def fetch_data_for_roles(
    stock_code: str,
    participants: list,
    summarizers: list,
) -> str:
    """根据所有角色的 allowed_dimensions 并集预取数据，返回格式化文本"""
    all_dims: set[str] = set()
    for r in participants + summarizers:
        all_dims.update(r.allowed_dimensions)

    print(f"[数据预取] 股票={stock_code}, 维度={sorted(all_dims)}")

    sections: list[str] = []
    success_count = 0
    fail_dimensions: list[str] = []

    for dim_name in sorted(all_dims):
        fetch_func = _get_fetch_function(dim_name)
        if fetch_func is None:
            fail_dimensions.append(dim_name)
            continue

        try:
            kwargs = _build_kwargs(fetch_func, stock_code)
            raw = fetch_func(**kwargs)
            formatted = _format_response(raw)
            sections.append(f"## {dim_name}\n\n{formatted}")
            success_count += 1
            row_count = _count_rows(raw)
            print(f"  [OK] {dim_name} — {row_count}")
        except Exception as e:
            print(f"[警告] 获取维度 {dim_name} 失败: {e}", file=sys.stderr)
            fail_dimensions.append(dim_name)
            sections.append(f"## {dim_name}\n\n（获取失败：{e}）")

    header = (
        f"# 股票数据报告\n\n"
        f"**股票代码**: {stock_code}\n"
        f"**获取时间**: 由 market_data 模块提供\n"
        f"**成功获取**: {success_count}/{len(all_dims)} 个维度\n\n"
        f"---\n"
    )

    body = "\n\n".join(sections)
    footer = ""

    if fail_dimensions:
        footer = f"\n\n---\n*注：以下维度获取失败：{', '.join(fail_dimensions)}*"

    return header + body + footer
