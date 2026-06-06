from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class EvaluationMetrics:
    """评测指标值对象 — 内聚检索评测结果"""

    retrieved_chunk_ids: list[str] = field(default_factory=list)
    is_hit: bool | None = None
    hit_rank: int | None = None
    evaluated_at: datetime | None = None

    def set_retrieved(self, ids: list[str]) -> None:
        """设置检索结果 ID 列表"""
        self.retrieved_chunk_ids = ids
