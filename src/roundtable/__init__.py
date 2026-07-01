"""Roundtable —— 简单 for 循环驱动的多角色圆桌讨论

使用方式:
    # Python API
    from roundtable import run_roundtable
    md_path = await run_roundtable(code="600519", rounds=3)

    # CLI
    python -m roundtable --code 600519 --rounds 3
"""

from pathlib import Path

from analyst_agents.role_loader import load_roles
from analyst_agents.state import AgentMessage, RoleConfig
from llm.client import call_claude

from .data_fetcher import fetch_data_for_roles
from .md_render import render_markdown


# ── 上下文构建 ─────────────────────────────────────────────────

def _build_history_text(history: list[AgentMessage]) -> str:
    if not history:
        return "（尚无发言）"
    lines: list[str] = []
    for msg in history:
        lines.append(
            f"**[第{msg['round']}轮] {msg['role_title']}（{msg['role_name']}）**：\n"
            f"{msg['content']}"
        )
    return "\n\n".join(lines)


def _filter_data_for_role(pre_fetched_data: str, allowed_dims: list[str]) -> str:
    if not allowed_dims:
        return "（无权限访问任何数据维度）"

    lines = pre_fetched_data.split("\n")
    result: list[str] = []
    current_section: list[str] = []
    include_section = False

    for line in lines:
        if line.startswith("## "):
            if include_section and current_section:
                result.extend(current_section)
            current_section = [line]
            dim_name = line[3:].strip()
            include_section = dim_name in set(allowed_dims)
        else:
            if include_section:
                current_section.append(line)

    if include_section and current_section:
        result.extend(current_section)

    return "\n".join(result) if result else "（该角色无数据维度权限）"


# ── 主函数 ─────────────────────────────────────────────────────

async def run_roundtable(
    code: str,
    rounds: int = 1,
    roles_dir: str | Path = "config/roles",
    output_dir: str | Path = ".",
    model: str = "sonnet",
) -> Path:
    if rounds < 1 or rounds > 10:
        raise ValueError(f"轮次必须在 1-10 之间，当前值: {rounds}")

    # 1. 加载角色
    participants, summarizers = load_roles(roles_dir)

    # 2. 预取数据
    pre_fetched_data = await fetch_data_for_roles(code, participants, summarizers)

    # 3. for 循环发言
    conversation_history: list[AgentMessage] = []

    for round_num in range(1, rounds + 1):
        for role in participants:
            history_text = _build_history_text(conversation_history)
            role_data = _filter_data_for_role(
                pre_fetched_data, role.allowed_dimensions
            )

            user_message = (
                f"# 任务\n\n"
                f"你正在参与一场关于股票 **{code}** 的多角色分析讨论。\n"
                f"这是第 **{round_num}** 轮发言（共 {rounds} 轮）。\n\n"
                f"## 你的角色\n\n"
                f"**{role.role}** —— 请从你的专业角度发表分析意见。\n\n"
                f"## 数据\n\n"
                f"{role_data}\n\n"
                f"## 已有讨论\n\n"
                f"{history_text}\n\n"
                f"请发表你的第 {round_num} 轮分析。控制在 400 字以内。"
            )

            content = await call_claude(role.system_prompt, user_message, model=model)

            new_msg: AgentMessage = {
                "round": round_num,
                "role_name": role.name,
                "role_title": role.role,
                "content": content,
            }
            conversation_history.append(new_msg)

            print(f"  [{round_num}轮] {role.role} 发言完成")
            print(f"  {'─' * 40}")
            print(content)
            print(f"  {'─' * 40}\n")

    # 4. 总结
    if not summarizers:
        final_summary = "（未配置总结角色）"
    else:
        summarizer_role = summarizers[0]
        history_text = _build_history_text(conversation_history)

        user_message = (
            f"# 总结任务\n\n"
            f"以下是关于股票 **{code}** 的 {rounds} 轮多角色分析讨论。\n"
            f"参与角色：{', '.join(r.role for r in participants)}。\n\n"
            f"## 完整讨论记录\n\n"
            f"{history_text}\n\n"
            f"## 数据报告\n\n"
            f"{pre_fetched_data}\n\n"
            f"请给出最终分析总结。控制在 600 字以内，包含：\n"
            f"1) 各角色核心观点提炼\n"
            f"2) 关键共识与分歧\n"
            f"3) 综合评估与建议"
        )

        final_summary = await call_claude(summarizer_role.system_prompt, user_message)

    # 5. 输出 Markdown
    output_path = Path(output_dir) / f"roundtable_{code}.md"
    md_path = render_markdown(
        stock_code=code,
        participants=participants,
        summarizers=summarizers,
        max_rounds=rounds,
        conversation_history=conversation_history,
        final_summary=final_summary,
        output_path=output_path,
    )

    return md_path
