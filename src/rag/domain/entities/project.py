from dataclasses import dataclass, field
from datetime import datetime

from rag.domain.value_objects.project_eval_summary import ProjectEvalSummary


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
    created_at: datetime | None = None
    updated_at: datetime | None = None
    eval_summary: ProjectEvalSummary | None = field(default=None, repr=False)

    # ── 修改规则 ──────────────────────────────────────────

    def update_profile(self, name: str, description: str) -> None:
        """更新项目基本信息 — 仅允许修改名称和描述，保护其他字段不变量"""
        self.name = name
        self.description = description

    def record_eval(self, summary: ProjectEvalSummary) -> None:
        """记录评测汇总 — 封装评测结果写入规则"""
        self.eval_summary = summary
