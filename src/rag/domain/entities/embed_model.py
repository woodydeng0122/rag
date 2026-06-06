from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ModelStatus(str, Enum):
    """模型状态枚举 — 避免魔法字符串"""
    ONLINE = "online"
    OFFLINE = "offline"


@dataclass
class EmbedModel:
    """嵌入模型实体 — 注册可用的 embedding 模型"""

    id: str = ""
    name: str = ""
    dimension: int = 0
    description: str = ""
    status: ModelStatus = ModelStatus.OFFLINE
    config: dict = field(default_factory=dict)  # config.json 原始内容
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def is_online(self) -> bool:
        return self.status == ModelStatus.ONLINE

    def go_online(self) -> None:
        self.status = ModelStatus.ONLINE

    def go_offline(self) -> None:
        self.status = ModelStatus.OFFLINE
