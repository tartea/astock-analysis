"""Roundtable —— 简单 for 循环驱动的多角色圆桌讨论

使用方式:
    # Python API
    from roundtable import run_roundtable
    md_path = await run_roundtable(code="600519", rounds=3)

    # CLI
    python -m roundtable --code 600519 --rounds 3
"""

from pathlib import Path

import yaml

from .role_loader import load_roles
from .state import AgentMessage, RoleConfig
from llm.client import call_claude

from .data_fetcher import fetch_data_for_roles
from .md_render import render_markdown


# ── Prompt 模板加载 ─────────────────────────────────────────────

def _load_prompt(name: str, prompts_dir: str | Path = "config/prompts") -> str:
    """从 YAML 文件加载 prompt 模板"""
    path = Path(prompts_dir) / f"{name}.yml"
    if not path.is_file():
        raise FileNotFoundError(f"Prompt 模板不存在: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["template"]


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
    if rounds < 1 or rounds > 100:
        raise ValueError(f"轮次必须在 1-10 之间，当前值: {rounds}")

    # 1. 加载角色
    participants, summarizers = load_roles(roles_dir)

    # 2. 预取数据
    pre_fetched_data = await fetch_data_for_roles(code, participants, summarizers)

    # 3. for 循环发言
    conversation_history: list[AgentMessage] = []
    speaker_tpl = _load_prompt("speaker")

    for round_num in range(1, rounds + 1):
        for role in participants:
            history_text = _build_history_text(conversation_history)
            role_data = _filter_data_for_role(
                pre_fetched_data, role.allowed_dimensions
            )

            user_message = speaker_tpl.format(
                code=code,
                round_num=round_num,
                rounds=rounds,
                role_name=role.name,
                role_title=role.role,
                role_data=role_data,
                history_text=history_text,
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
        summarizer_tpl = _load_prompt("summarizer")

        user_message = summarizer_tpl.format(
            code=code,
            rounds=rounds,
            participants=", ".join(r.role for r in participants),
            history_text=history_text,
            pre_fetched_data=pre_fetched_data,
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
