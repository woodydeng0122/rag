from dataclasses import dataclass
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
