from dataclasses import dataclass


@dataclass
class Profile:
    """用户配置实体 — 单例，仅存储激活项目 ID"""
    id: int = 1
    active_project_id: str = ""
