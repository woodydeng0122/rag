from dataclasses import dataclass

from rag.domain.value_objects.retrieval_result import RetrievalResult


@dataclass
class RetrievalOutput:
    """检索输出 — 携带检索结果和分阶段耗时"""

    results: list[RetrievalResult]
    embed_latency_ms: int
    search_latency_ms: int
