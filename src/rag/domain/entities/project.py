from dataclasses import dataclass
from datetime import datetime


@dataclass
class Project:
    """项目实体 — 一个项目包含多文档

    充血模型：封装永远成立的约束和纯函数性质的业务规则。
    业务场景的流程、需要外部信息的决策留在 Use Case。
    """

    id: str = ""
    name: str = ""
    description: str = ""
    embed_model_id: str = ""
    embed_dimension: int = 512
    rerank_model_id: str = ""
    user_id: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None

    # ── 修改规则 ──────────────────────────────────────────

    def update_profile(self, name: str, description: str) -> None:
        """更新项目基本信息 — 仅允许修改名称和描述，保护其他字段不变量"""
        self.name = name
        self.description = description
