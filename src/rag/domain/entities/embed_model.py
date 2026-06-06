from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ModelStatus(str, Enum):
    """模型状态枚举 — 避免魔法字符串"""
    ONLINE = "online"
    OFFLINE = "offline"


@dataclass
class EmbedModel:
    """嵌入模型实体 — 注册可用的 embedding 模型

    充血模型：封装永远成立的约束和纯函数性质的业务规则。
    业务场景的流程、需要外部信息的决策留在 Use Case。
    """

    id: str = ""
    name: str = ""
    dimension: int = 0
    description: str = ""
    status: ModelStatus = ModelStatus.OFFLINE
    config: dict = field(default_factory=dict)  # config.json 原始内容
    created_at: datetime | None = None
    updated_at: datetime | None = None

    # ── 状态查询 ──────────────────────────────────────────

    @property
    def is_online(self) -> bool:
        """status=ONLINE 即为在线 — 状态定义本身"""
        return self.status == ModelStatus.ONLINE

    # ── 状态变更 ──────────────────────────────────────────

    def go_online(self) -> None:
        self.status = ModelStatus.ONLINE

    def go_offline(self) -> None:
        self.status = ModelStatus.OFFLINE

    # ── 永远成立的约束 ────────────────────────────────────

    def ensure_complete(self) -> None:
        """校验模型完整性 — 维度不能为零，任何场景都应遵守"""
        if not self.dimension:
            raise ValueError("无法确定向量维度：本地未找到模型且未指定 dimension")

    # ── 修改规则 ──────────────────────────────────────────

    def update_profile(self, name: str, description: str) -> None:
        """更新模型基本信息 — 仅允许修改名称和备注，保护其他字段不变量"""
        self.name = name
        self.description = description
