from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from rag.domain.value_objects.retrieval_strategy import RetrievalStrategy


class EvaluationCategory(str, Enum):
    """评估类别 — 区分粗排评估和重排评估"""
    RECALL = "recall"
    RERANK = "rerank"


@dataclass
class ProjectEvaluation:
    """项目评估统计实体 — 记录一次评估的快照指标"""

    project_id: str
    top_k: int
    golden_total: int
    golden_retrieved: int
    recall_at_k: float
    mrr: float
    ndcg: float
    hit_rate: float
    full_hit_count: int
    zero_hit_count: int
    avg_latency_ms: float
    avg_embed_latency_ms: float
    avg_search_latency_ms: float
    category: EvaluationCategory = EvaluationCategory.RECALL
    strategy: RetrievalStrategy = RetrievalStrategy.HYBRID
    embed_model_name: str = ""
    remark: str = ""
    id: str = ""
    created_at: datetime | None = None
