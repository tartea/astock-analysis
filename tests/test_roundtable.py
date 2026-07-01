"""Roundtable 模块测试 —— mock call_claude 验证编排正确性"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# roundtable/__init__.py → llm.client → claude_agent_sdk 不在测试环境。
# 在 import 之前注入 mock。
for _mod in ("claude_agent_sdk",):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

from roundtable.state import AgentMessage, RoleConfig


# ── 角色工厂 ───────────────────────────────────────────────────

def _make_role(name: str, order: int, allowed_dims: list[str] | None = None) -> RoleConfig:
    return RoleConfig(
        name=name,
        role=name,
        system_prompt=f"你是{name}",
        allowed_dimensions=allowed_dims or ["kline"],
        speaking_order=order,
        yaml_path="",
    )


# ── 历史文本构建测试 ───────────────────────────────────────────

class TestBuildHistoryText:
    def test_empty_history(self):
        from roundtable import _build_history_text
        result = _build_history_text([])
        assert result == "（尚无发言）"

    def test_single_message(self):
        from roundtable import _build_history_text
        msg: AgentMessage = {
            "round": 1, "role_name": "tech", "role_title": "技术分析师", "content": "看涨"
        }
        result = _build_history_text([msg])
        assert "第1轮" in result
        assert "技术分析师" in result
        assert "看涨" in result

    def test_multiple_messages_cross_round(self):
        from roundtable import _build_history_text
        msgs: list[AgentMessage] = [
            {"round": 1, "role_name": "tech", "role_title": "技术", "content": "先发言"},
            {"round": 1, "role_name": "fund", "role_title": "基本面", "content": "第2个"},
            {"round": 2, "role_name": "tech", "role_title": "技术", "content": "再次发言"},
        ]
        result = _build_history_text(msgs)
        assert "第1轮" in result
        assert "第2轮" in result
        assert "先发言" in result
        assert "再次发言" in result


# ── 数据筛选测试 ───────────────────────────────────────────────

class TestFilterDataForRole:
    def test_filters_sections_by_allowed_dims(self):
        from roundtable import _filter_data_for_role
        data = (
            "## kline\nkline数据内容\n\n"
            "## sentiment\n情绪数据内容\n\n"
            "## news\n新闻数据内容\n"
        )
        result = _filter_data_for_role(data, ["kline", "news"])
        assert "kline数据内容" in result
        assert "新闻数据内容" in result
        assert "情绪数据内容" not in result

    def test_empty_allowed_dims(self):
        from roundtable import _filter_data_for_role
        result = _filter_data_for_role("## kline\n数据", [])
        assert "无权限" in result


# ── Markdown 渲染测试 ──────────────────────────────────────────

class TestMarkdownRender:
    def test_output_structure(self, tmp_path):
        from roundtable.md_render import render_markdown

        participants = [
            _make_role("技术面分析师", 1),
            _make_role("基本面分析师", 2),
        ]
        summarizers = [_make_role("首席策略师", 999)]

        history: list[AgentMessage] = [
            {"round": 1, "role_name": "技术面分析师", "role_title": "技术面分析师", "content": "看多"},
            {"round": 1, "role_name": "基本面分析师", "role_title": "基本面分析师", "content": "估值合理"},
        ]

        output = tmp_path / "test.md"
        result = render_markdown(
            stock_code="600519",
            participants=participants,
            summarizers=summarizers,
            max_rounds=1,
            conversation_history=history,
            final_summary="综合推荐买入",
            output_path=output,
        )

        content = result.read_text(encoding="utf-8")
        assert "600519" in content
        assert "技术面分析师" in content
        assert "基本面分析师" in content
        assert "看多" in content
        assert "估值合理" in content
        assert "综合推荐买入" in content
        assert "参与角色" in content
        assert "第 1 轮" in content
        assert "最终总结" in content

    def test_multi_round_grouping(self, tmp_path):
        from roundtable.md_render import render_markdown

        participants = [_make_role("技术面分析师", 1)]
        summarizers = [_make_role("首席策略师", 999)]

        history: list[AgentMessage] = [
            {"round": 1, "role_name": "技术面分析师", "role_title": "技术面分析师", "content": "第一轮"},
            {"round": 2, "role_name": "技术面分析师", "role_title": "技术面分析师", "content": "第二轮"},
        ]

        output = tmp_path / "test_multi.md"
        result = render_markdown(
            stock_code="000001",
            participants=participants,
            summarizers=summarizers,
            max_rounds=2,
            conversation_history=history,
            final_summary="总结",
            output_path=output,
        )

        content = result.read_text(encoding="utf-8")
        assert "第 1 轮" in content
        assert "第 2 轮" in content
        assert "第一轮" in content
        assert "第二轮" in content


# ── 端到端编排测试 ─────────────────────────────────────────────

class TestRunRoundtable:
    @pytest.mark.asyncio
    async def test_orchestration_order(self, tmp_path, monkeypatch):
        """验证发言按轮次 × speaking_order 顺序调用，历史累积正确"""
        from roundtable import run_roundtable

        call_count = 0
        call_args: list[dict] = []

        async def fake_call_claude(system_prompt, user_message, model="sonnet"):
            nonlocal call_count
            call_count += 1
            call_args.append({
                "system_prompt": system_prompt,
                "user_message": user_message,
                "model": model,
            })
            return f"发言内容-{call_count}"

        monkeypatch.setattr("roundtable.call_claude", fake_call_claude)

        async def fake_fetch(stock_code, participants, summarizers):
            return "预取数据"

        monkeypatch.setattr("roundtable.fetch_data_for_roles", fake_fetch)

        participants = [
            _make_role("技术面分析师", 1, ["kline"]),
            _make_role("基本面分析师", 2, ["financials"]),
        ]
        summarizers = [_make_role("首席策略师", 999, ["kline", "financials"])]

        monkeypatch.setattr(
            "roundtable.load_roles",
            lambda roles_dir: (participants, summarizers),
        )

        result = await run_roundtable(
            code="600519",
            rounds=2,
            output_dir=str(tmp_path),
            model="sonnet",
        )

        # 2 rounds × 2 participants + 1 summarizer = 5 calls
        assert call_count == 5

        # 第1轮第1个发言：历史为空
        assert "尚无发言" in call_args[0]["user_message"]
        # 第1轮第2个发言：包含第1个发言的历史
        assert "发言内容-1" in call_args[1]["user_message"]
        # 第2轮第1个发言：包含前2条历史（跨轮累积）
        assert "发言内容-1" in call_args[2]["user_message"]
        assert "发言内容-2" in call_args[2]["user_message"]
        # 第2轮第2个发言：包含前3条历史
        assert "发言内容-3" in call_args[3]["user_message"]
        # 总结人：包含全部4条
        assert "发言内容-4" in call_args[4]["user_message"]

        assert result.exists()
        assert result.suffix == ".md"
        assert "roundtable_600519" in result.name

    @pytest.mark.asyncio
    async def test_no_summarizer(self, tmp_path, monkeypatch):
        from roundtable import run_roundtable

        call_count = 0

        async def fake_call_claude(system_prompt, user_message, model="sonnet"):
            nonlocal call_count
            call_count += 1
            return f"发言-{call_count}"

        async def fake_fetch(stock_code, participants, summarizers):
            return "数据"

        monkeypatch.setattr("roundtable.call_claude", fake_call_claude)
        monkeypatch.setattr("roundtable.fetch_data_for_roles", fake_fetch)
        monkeypatch.setattr(
            "roundtable.load_roles",
            lambda roles_dir: ([_make_role("技术面分析师", 1)], []),
        )

        result = await run_roundtable(
            code="000001",
            rounds=1,
            output_dir=str(tmp_path),
        )

        assert call_count == 1
        content = result.read_text(encoding="utf-8")
        assert "未配置总结角色" in content

    @pytest.mark.asyncio
    async def test_rounds_validation(self, tmp_path, monkeypatch):
        from roundtable import run_roundtable

        monkeypatch.setattr(
            "roundtable.load_roles",
            lambda roles_dir: ([_make_role("技术面分析师", 1)], [_make_role("首席策略师", 999)]),
        )

        with pytest.raises(ValueError, match="轮次必须在 1-"):
            await run_roundtable(code="600519", rounds=0, output_dir=str(tmp_path))

        with pytest.raises(ValueError, match="轮次必须在 1-"):
            await run_roundtable(code="600519", rounds=101, output_dir=str(tmp_path))
