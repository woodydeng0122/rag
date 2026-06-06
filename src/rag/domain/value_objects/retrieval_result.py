from dataclasses import dataclass


@dataclass
class RetrievalResult:
    """检索结果值对象 — 关联 chunk_id 与相似度得分"""

    chunk_id: str
    score: float
