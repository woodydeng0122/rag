from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class GoldenStatus(str, Enum):
    """黄金记录状态枚举 — 避免魔法字符串"""

    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


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


@dataclass
class GoldenRecord:
    """评测黄金记录实体 — 含查询、真实分块、参考答案"""

    query: str
    ground_truth_chunks: list[str] = field(default_factory=list)
    reference_answer: str = ""
    id: str = ""
    project_id: str = ""
    status: GoldenStatus = GoldenStatus.APPROVED
    evaluation: EvaluationMetrics | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    metadata: dict = field(default_factory=dict)
