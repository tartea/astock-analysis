"""Claude Agent SDK 公共调用模块 —— 供 analyst_agents 和 roundtable 复用"""

from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
)


async def call_claude(
    system_prompt: str,
    user_message: str,
    model: str = "sonnet",
) -> str:
    """使用 Claude Agent SDK 的 query() 调用 Claude，收集文本响应"""
    parts: list[str] = []

    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        allowed_tools=[],
        permission_mode="dontAsk",
        model=model,
    )

    async for message in query(prompt=user_message, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    parts.append(block.text)

    return "".join(parts)
