import asyncio

from rag.domain.value_objects.retrieval_result import RetrievalResult
from rag.domain.value_objects.retrieval_output import RetrievalOutput
from rag.domain.ports.retriever import RetrieverPort
from rag.shared.logger import logger
from rag.shared.timer import measure


class HybridRetriever(RetrieverPort):
    """混合检索器 — Vector + BM25 双路召回，RRF 融合排序

    RRF (Reciprocal Rank Fusion) 公式：
        score(d) = Σ 1 / (k + rank_i(d))

    k 越小，融合对排名差异越敏感。
    当 chunk 同时出现在两路时，得分 = 1/(k+rank_vector) + 1/(k+rank_bm25)，
    显著高于单路命中的 chunk，实现"两路都认可则优先"的效果。

    每路按 overretrieve_factor 倍过量召回，融合后再截断到 top_k，
    避免 GT chunk 因单路排名靠后被提前截断。
    """

    def __init__(
        self,
        vector_retriever: RetrieverPort,
        bm25_retriever: RetrieverPort,
        rrf_k: float = 1.0,
        overretrieve_factor: int = 3,
    ):
        self._vector = vector_retriever
        self._bm25 = bm25_retriever
        self._rrf_k = rrf_k
        self._overretrieve_factor = overretrieve_factor

    async def retrieve(self, query: str, project_id: str, top_k: int = 3) -> RetrievalOutput:
        logger.info({"message": f"检索策略=HybridRetriever, project_id={project_id}, top_k={top_k}, query={query[:50]}"})
        timings: dict[str, int] = {}

        fetch_k = top_k * self._overretrieve_factor

        with measure(timings, "search"):
            vector_output, bm25_output = await asyncio.gather(
                self._vector.retrieve(query, project_id, fetch_k),
                self._bm25.retrieve(query, project_id, fetch_k),
            )

        # RRF 融合：两路得分各自归一化后相加
        scores: dict[str, float] = {}
        for rank, r in enumerate(vector_output.results, start=1):
            scores[r.chunk_id] = scores.get(r.chunk_id, 0) + 1.0 / (self._rrf_k + rank)
        for rank, r in enumerate(bm25_output.results, start=1):
            scores[r.chunk_id] = scores.get(r.chunk_id, 0) + 1.0 / (self._rrf_k + rank)

        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        results = [
            RetrievalResult(chunk_id=chunk_id, score=score)
            for chunk_id, score in sorted_results
        ]

        return RetrievalOutput(
            results=results,
            embed_latency_ms=vector_output.embed_latency_ms,
            search_latency_ms=vector_output.search_latency_ms + bm25_output.search_latency_ms,
        )
