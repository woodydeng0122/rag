from dataclasses import dataclass


@dataclass
class GoldenRerankItem:
    """重排结果明细 — 单个重排后的 chunk 及其得分和排名"""

    rerank_id: str
    chunk_id: str
    original_rank: int
    rerank_score: float
    rerank_rank: int
    id: str = ""
