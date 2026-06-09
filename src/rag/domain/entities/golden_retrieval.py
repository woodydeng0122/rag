from dataclasses import dataclass
from datetime import datetime


@dataclass
class GoldenRetrieval:
    """黄金记录检索结果实体 — 记录一次检索的指标"""

    golden_id: str
    max_k: int
    latency_ms: int
    embed_model_name: str
    id: str = ""
    created_at: datetime | None = None
