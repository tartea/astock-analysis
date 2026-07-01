"""Markdown 报告生成器 —— 将对话记录渲染为 Markdown 文件"""

from pathlib import Path

from .state import AgentMessage, RoleConfig


def render_markdown(
    stock_code: str,
    participants: list[RoleConfig],
    summarizers: list[RoleConfig],
    max_rounds: int,
    conversation_history: list[AgentMessage],
    final_summary: str,
    output_path: str | Path,
) -> Path:
    output_path = Path(output_path)

    lines: list[str] = []
    lines.append(f"# 圆桌讨论报告 — {stock_code}")
    lines.append("")

    # 参与角色
    lines.append("## 参与角色")
    lines.append("")
    for r in participants:
        dims = ", ".join(r.allowed_dimensions)
        lines.append(f"- **{r.role}** ({r.name}) — 发言顺序: {r.speaking_order}, 数据维度: {dims}")
    lines.append("")

    # 按轮次分组发言
    rounds: dict[int, list[AgentMessage]] = {}
    for msg in conversation_history:
        rounds.setdefault(msg["round"], []).append(msg)

    for round_num in sorted(rounds.keys()):
        lines.append(f"## 第 {round_num} 轮")
        lines.append("")
        for msg in rounds[round_num]:
            lines.append(f"### {msg['role_title']}（{msg['role_name']}）")
            lines.append("")
            lines.append(msg["content"])
            lines.append("")

    # 最终总结
    summarizer_name = summarizers[0].role if summarizers else "总结"
    lines.append(f"## 最终总结（{summarizer_name}）")
    lines.append("")
    lines.append(final_summary if final_summary else "（无总结内容）")
    lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[Markdown] 报告已生成: {output_path}")
    return output_path
