from dataclasses import dataclass

from rag.domain.value_objects.retrieval_result import RetrievalResult


@dataclass
class RetrievalOutput:
    """检索输出 — 携带检索结果和分阶段耗时"""

    results: list[RetrievalResult]
    embed_latency_ms: int
    search_latency_ms: int
    load_embeddings_latency_ms: int = 0
    load_project_latency_ms: int = 0
    load_embed_model_latency_ms: int = 0
    get_embedder_latency_ms: int = 0
    build_matrix_latency_ms: int = 0
