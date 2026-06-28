"""Type definitions for industry board dimension responses."""

from __future__ import annotations

from typing import TypedDict


class IndustryBoardItem(TypedDict):
    """行业板块列表项（无 board_name 时，来自东方财富）."""

    排名: int
    板块名称: str
    板块代码: str
    最新价: float
    涨跌额: float
    涨跌幅: float
    总市值: float
    换手率: float
    上涨家数: int
    下跌家数: int
    领涨股票: str


# 领涨股票-涨跌幅 含连字符，需用赋值语法追加
IndustryBoardItem.__annotations__["领涨股票-涨跌幅"] = float


class IndustryBoardHistItem(TypedDict):
    """行业板块历史行情项（有 board_name 时）."""

    日期: str
    开盘: float
    收盘: float
    最高: float
    最低: float
    涨跌幅: float
    涨跌额: float
    成交量: float
    成交额: float
    振幅: float
    换手率: float


class IndustryBoardThsItem(TypedDict):
    """行业板块列表项（THS 同花顺降级时返回）."""

    name: str
    code: str


IndustryDataItem = IndustryBoardItem | IndustryBoardHistItem | IndustryBoardThsItem
"""行业板块数据项联合类型."""


class IndustryResponse(TypedDict):
    """Industry board data response."""

    data: list[IndustryDataItem]
    provider: str
    board_name: str
