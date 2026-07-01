"""角色加载器 —— 扫描 YAML 文件夹 → 解析 → 四种校验 → 返回 RoleConfig"""

import sys
from pathlib import Path

import yaml

from .state import RoleConfig


def _discover_available_dimensions() -> list[str]:
    """从 market_data.dimensions 包中动态发现所有可用维度名"""
    try:
        from market_data import dimensions
        pkg_dir = Path(dimensions.__path__[0])
        dims: list[str] = []
        for entry in pkg_dir.iterdir():
            if entry.is_dir() and not entry.name.startswith("_"):
                dims.append(entry.name)
        return sorted(dims)
    except ImportError:
        return sorted([
            "block_trade", "bond_convertible", "capital_flow",
            "concept", "financials", "fund", "futures",
            "holder", "index", "industry", "ipo",
            "kline", "lhb", "margin", "news",
            "north_flow", "realtime", "sentiment", "stock_info",
        ])


def _validate_roles(
    participants: list[RoleConfig],
    summarizers: list[RoleConfig],
    available_dims: list[str],
) -> None:
    """四种启动校验：冲突/重复/无效/断号，任一失败即 sys.exit(1)"""

    all_roles = participants + summarizers
    errors: list[str] = []

    # 1. 角色名重复检测
    seen: dict[str, str] = {}
    for r in all_roles:
        if r.name in seen:
            errors.append(
                f"角色名重复：\"{r.name}\" 在 {seen[r.name]} 和 {r.yaml_path} 中各出现一次"
            )
        seen[r.name] = r.yaml_path

    # 2. 无效维度检测
    for r in all_roles:
        for dim in r.allowed_dimensions:
            if dim not in available_dims:
                errors.append(
                    f"角色 \"{r.name}\" 包含无效维度 \"{dim}\"，"
                    f"可用维度：{available_dims}"
                )

    # 3. 发言顺序冲突检测（仅 participant）
    order_to_role: dict[int, str] = {}
    for r in participants:
        if r.speaking_order in order_to_role:
            errors.append(
                f"发言顺序冲突：角色 \"{r.name}\" 和 \"{order_to_role[r.speaking_order]}\" "
                f"的 speaking_order={r.speaking_order} 重复"
            )
        order_to_role[r.speaking_order] = r.name

    # 4. 发言顺序断号检测（仅 participant）
    if participants:
        orders = sorted(r.speaking_order for r in participants)
        expected = list(range(1, len(participants) + 1))
        if orders != expected:
            for i, exp in enumerate(expected):
                if i >= len(orders) or orders[i] != exp:
                    prev = orders[i - 1] if i > 0 else 0
                    errors.append(
                        f"发言顺序不连续：缺少 order={exp}。"
                        f"检测到：order={prev} → order={orders[i] if i < len(orders) else '无'}"
                    )
                    break

    if errors:
        print("\n[角色配置校验失败]\n", file=sys.stderr)
        for i, err in enumerate(errors, 1):
            print(f"  {i}. {err}", file=sys.stderr)
        print(f"\n共 {len(errors)} 项错误，程序终止。\n", file=sys.stderr)
        sys.exit(1)


def load_roles(roles_dir: str | Path) -> tuple[list[RoleConfig], list[RoleConfig]]:
    """扫描 roles 文件夹，加载参与者与总结者角色

    Args:
        roles_dir: 根目录，其下应有 participants/ 和 summarizers/ 子文件夹

    Returns:
        (participants, summarizers) 两个 RoleConfig 列表，
        participants 已按 speaking_order 排序
    """
    root = Path(roles_dir)
    if not root.is_dir():
        print(f"[错误] 角色目录不存在: {root}", file=sys.stderr)
        sys.exit(1)

    participants: list[RoleConfig] = []
    summarizers: list[RoleConfig] = []

    for category, target_list in [
        ("participants", participants),
        ("summarizers", summarizers),
    ]:
        cat_dir = root / category
        if not cat_dir.is_dir():
            print(f"[警告] 角色目录不存在: {cat_dir}，跳过", file=sys.stderr)
            continue

        for yaml_file in sorted(cat_dir.glob("*.yml")):
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                print(f"[警告] {yaml_file} 为空，跳过", file=sys.stderr)
                continue

            config = RoleConfig(
                name=data.get("name", yaml_file.stem),
                role=data.get("role", ""),
                system_prompt=data.get("system_prompt", ""),
                allowed_dimensions=data.get("allowed_dimensions", []),
                speaking_order=data.get("speaking_order", 999) if category == "participants" else 999,
                yaml_path=str(yaml_file),
            )
            target_list.append(config)

        if not target_list and category == "participants":
            print(f"[错误] 未找到任何参与者角色文件 ({cat_dir}/*.yml)", file=sys.stderr)
            sys.exit(1)

    participants.sort(key=lambda r: r.speaking_order)

    available_dims = _discover_available_dimensions()
    _validate_roles(participants, summarizers, available_dims)

    print(f"[角色加载] participants={len(participants)}, summarizers={len(summarizers)}, "
          f"可用维度={len(available_dims)}")

    return participants, summarizers
