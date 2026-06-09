from dataclasses import dataclass


@dataclass
class GoldenRetrievalItem:
    """检索结果明细 — 单个检索到的 chunk 及其得分和排名"""

    retrieval_id: str
    chunk_id: str
    score: float
    rank: int
    id: str = ""
