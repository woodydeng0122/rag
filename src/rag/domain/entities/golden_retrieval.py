from dataclasses import dataclass
from datetime import datetime


@dataclass
class GoldenRetrieval:
    """黄金记录检索结果实体 — 记录一次检索的指标"""

    golden_id: str
    max_k: int
    latency_ms: int
    embed_model_name: str
    embed_latency_ms: int = 0
    search_latency_ms: int = 0
    id: str = ""
    created_at: datetime | None = None
