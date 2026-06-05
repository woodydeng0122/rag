from dataclasses import dataclass
from datetime import datetime


@dataclass
class EmbedModel:
    """嵌入模型实体 — 注册可用的 embedding 模型"""
    id: str = ""
    name: str = ""
    dimension: int = 0
    description: str = ""
    status: str = "offline"  # online / offline
    created_at: datetime | None = None
    updated_at: datetime | None = None
