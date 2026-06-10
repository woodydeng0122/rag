from dataclasses import dataclass


@dataclass
class Profile:
    """用户配置实体 — per-user，每个用户一行配置"""

    id: str = ""
    user_id: str = ""
    active_project_id: str | None = None
