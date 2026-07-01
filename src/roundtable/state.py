"""Roundtable 状态模型与角色配置 —— 自包含，无外部依赖"""

from dataclasses import dataclass
from typing import TypedDict


@dataclass
class RoleConfig:
    """单个角色的配置，从 YAML 文件解析而来"""
    name: str                           # 角色名称（唯一标识）
    role: str                           # 角色定位（如 "技术面分析师"）
    system_prompt: str                  # 系统提示词
    allowed_dimensions: list[str]       # 可访问的数据维度
    speaking_order: int                 # 发言顺序（仅 participant 有效）
    yaml_path: str = ""                 # YAML 文件来源路径（加载时记录）


class AgentMessage(TypedDict):
    """单条交流消息"""
    round: int                          # 所属轮次（从 1 开始）
    role_name: str                      # 发言角色名称
    role_title: str                     # 发言角色定位
    content: str                        # 发言内容
