from dataclasses import dataclass
from datetime import datetime

from rag.domain.value_objects.retrieval_strategy import RetrievalStrategy


@dataclass
class GoldenRetrieval:
    """黄金记录检索结果实体 — 记录一次检索的指标"""

    golden_id: str
    max_k: int
    latency_ms: int
    embed_model_name: str
    strategy: RetrievalStrategy = RetrievalStrategy.HYBRID
    embed_latency_ms: int = 0
    search_latency_ms: int = 0
    load_embeddings_latency_ms: int = 0
    load_project_latency_ms: int = 0
    load_embed_model_latency_ms: int = 0
    get_embedder_latency_ms: int = 0
    build_matrix_latency_ms: int = 0
    id: str = ""
    created_at: datetime | None = None
