from dataclasses import dataclass
from datetime import datetime


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
    # 评测汇总字段
    eval_recall_at_10: float | None = None
    eval_mrr: float | None = None
    eval_answerable: int | None = None
    eval_total: int | None = None
    eval_latency_avg_ms: float | None = None
    evaluated_at: datetime | None = None
