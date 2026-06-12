from dataclasses import dataclass


@dataclass
class RerankResult:
    """重排结果项 — 单个文档的 cross-encoder 分数"""

    index: int
    score: float
