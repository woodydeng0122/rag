from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ProjectEvalSummary:
    """项目评测汇总值对象 — 独立于项目元数据，评测指标变更不影响 Project"""
    recall_at_10: float | None = None
    mrr: float | None = None
    answerable: int | None = None
    total: int | None = None
    latency_avg_ms: float | None = None
    evaluated_at: datetime | None = None


@dataclass
class Project:
    """项目实体 — 一个项目包含多文档"""
    id: str = ""
    name: str = ""
    description: str = ""
    embed_model_id: str = ""
    embed_dimension: int = 512
    created_at: datetime | None = None
    updated_at: datetime | None = None
    eval_summary: ProjectEvalSummary | None = field(default=None, repr=False)
