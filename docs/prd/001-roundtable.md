# PRD: Roundtable — 简单多角色圆桌讨论

## Problem Statement

现有的 `analyst_agents` 使用 LangGraph 编排多角色讨论流程，对于一个简单的、纯 for 循环驱动的多角色圆桌讨论场景，LangGraph 引入了不必要的复杂度和依赖。用户需要一个独立、轻量、易于理解和修改的替代方案，实现相同的核心能力：加载角色配置 → 预取数据 → 按序发言（历史累积）→ 多轮迭代 → 总结人收尾。

## Solution

在 `src/roundtable/` 下新建独立模块，用裸 for 循环替代 LangGraph 编排。同时将 Claude 调用提取到 `src/llm/client.py` 公共组件，供 `analyst_agents` 和 `roundtable` 共同使用。输出 Markdown 格式报告。

## User Stories

1. As a 用户，我希望通过 CLI 传入股票代码和轮次，运行圆桌讨论，生成 Markdown 报告
2. As a 用户，我希望讨论过程中每个角色按 `speaking_order` 顺序依次发言
3. As a 用户，我希望每个角色发言时能看到之前所有人的发言内容（跨轮累积）
4. As a 用户，我希望所有发言完成后，由配置的总结角色生成最终总结
5. As a 用户，我希望输出的 Markdown 报告包含参与角色列表、每轮发言内容、最终总结
6. As a 用户，我希望能在 CLI 指定角色配置目录（`--roles-dir`）
7. As a 用户，我希望能在 CLI 选择 Claude 模型（`--model`）
8. As a 用户，我希望能在 CLI 指定输出目录（`--output-dir`）
9. As a 开发者，我希望 Claude 调用逻辑是独立公共组件，`analyst_agents` 和 `roundtable` 都能复用
10. As a 用户，我希望 `roundtable` 的 CLI 参数和 `analyst_agents` 保持一致（参数名和语义相同）
11. As a 用户，我希望角色配置 YAML 文件能被 `analyst_agents` 和 `roundtable` 共享解析
12. As a 用户，我希望数据预取在循环开始前一次性完成，不逐次请求

## Implementation Decisions

1. **模块结构**：新增 `src/roundtable/` 包（与 `analyst_agents` 平级）和 `src/llm/` 公共组件
2. **编排方式**：裸 for 循环，`for round in range(rounds): for role in participants: ...`，不使用 LangGraph
3. **角色加载**：复用 `analyst_agents.role_loader.load_roles()`，不重复实现 YAML 解析和校验
4. **数据获取**：在 `roundtable` 内部重新实现（动态 import `market_data.dimensions` + 签名推断），不依赖 `analyst_agents.data_prep`
5. **历史累积**：`conversation_history: list` 跨轮追加，每个角色发言时拼接历史文本注入 prompt
6. **Claude 调用**：提取为 `src/llm/client.py` 的 `call_claude(system_prompt, user_message, model) -> str` 异步函数，使用 `claude_agent_sdk.query()`，`allowed_tools=[]`、`permission_mode="dontAsk"`
7. **`analyst_agents` 适配**：将其内部的 `_call_claude` 调用替换为从 `src.llm.client` import
8. **输出格式**：Markdown 文件，结构为：标题 → 参与角色 → 每轮发言（按序）→ 最终总结
9. **CLI 入口**：`python -m roundtable --code 600519 --rounds 3`，参数签名和 `analyst_agents` 一致（`--code`、`--rounds`、`--roles-dir`、`--output-dir`、`--model`）
10. **轮次默认值**：`--rounds` 默认 1（和 `analyst_agents` 默认 3 不同，体现简单场景）
11. **输出文件名**：`roundtable_{code}.md`，不可通过 CLI 指定

## Testing Decisions

- **测试策略**：只测试外部可观察行为，不测内部实现细节
- **最高接缝**：mock `call_claude` 返回固定文本，端到端测试 `run_roundtable()` 的编排正确性
- **测试内容**：角色加载校验、历史累积顺序、Markdown 输出结构、CLI 参数解析
- **复用参考**：项目现有测试 `tests/test_core.py` 的 pytest 风格

## Out of Scope

- HTML 报告生成（`roundtable` 只输出 Markdown）
- 修改 `analyst_agents` 的 LangGraph 编排逻辑（仅替换其 Claude 调用为公共组件）
- 支持流式输出
- 支持非 Claude 的 LLM provider

## Further Notes

- `src/llm/client.py` 是纯函数封装，不引入新的抽象层（如 adapter pattern），保持简单
- `analyst_agents` 的 `__init__.py` 和 `graph.py` 需要小幅修改以使用公共组件替换内部的 `_call_claude`
