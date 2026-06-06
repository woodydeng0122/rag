from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from rag.domain.value_objects.model_config import ModelConfig


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
    config: ModelConfig = field(default_factory=ModelConfig)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self):
        self.ensure_complete()

    @classmethod
    def reconstruct(
        cls,
        *,
        id: str,
        name: str,
        dimension: int,
        description: str,
        status: ModelStatus,
        config: ModelConfig,
        created_at: datetime | None,
        updated_at: datetime | None,
    ) -> "EmbedModel":
        """从持久化层重建 — 不执行业务校验，信任数据源"""
        obj = object.__new__(cls)
        obj.id = id
        obj.name = name
        obj.dimension = dimension
        obj.description = description
        obj.status = status
        obj.config = config
        obj.created_at = created_at
        obj.updated_at = updated_at
        return obj

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
