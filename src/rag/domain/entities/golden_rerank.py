from dataclasses import dataclass
from datetime import datetime


@dataclass
class GoldenRerank:
    """黄金记录重排结果实体 — 记录一次重排的指标"""

    golden_id: str
    top_k: int
    latency_ms: int
    model_name: str
    id: str = ""
    created_at: datetime | None = None
