from dataclasses import dataclass


@dataclass
class RetrievedChunk:
    """单个检索到的分块结果"""
    chunk_id: str
    content: str
    source_file: str
    heading: str
    score: float


@dataclass
class RetrieveResult:
    """检索结果 — 用例的输出，纯业务数据"""
    chunks: list[RetrievedChunk]
