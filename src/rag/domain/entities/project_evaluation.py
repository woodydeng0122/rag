from dataclasses import dataclass
from datetime import datetime


@dataclass
class ProjectEvaluation:
    """项目评估统计实体 — 记录一次评估的快照指标"""

    project_id: str
    top_k: int
    golden_total: int
    golden_retrieved: int
    recall_at_k: float
    mrr: float
    hit_rate: float
    full_hit_count: int
    zero_hit_count: int
    avg_latency_ms: float
    avg_embed_latency_ms: float
    avg_search_latency_ms: float
    embed_model_name: str = ""
    id: str = ""
    created_at: datetime | None = None
