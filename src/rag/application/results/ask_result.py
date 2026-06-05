from dataclasses import dataclass


@dataclass
class ChunkResult:
    """单个检索结果"""
    chunk_id: str
    content: str
    score: float


@dataclass
class AskResult:
    """问答结果 — 用例的输出，纯业务数据"""
    answer: str
    chunks: list[ChunkResult]
