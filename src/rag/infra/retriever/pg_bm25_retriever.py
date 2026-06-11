from rag.domain.value_objects.retrieval_result import RetrievalResult
from rag.domain.value_objects.retrieval_output import RetrievalOutput
from rag.domain.ports.chunk_repository import ChunkRepositoryPort
from rag.domain.ports.retriever import RetrieverPort
from rag.shared.logger import logger
from rag.shared.timer import measure


class PgBm25Retriever(RetrieverPort):
    """基于 PostgreSQL ts_vector 全文检索的 BM25 检索器"""

    def __init__(self, chunk_repo: ChunkRepositoryPort):
        self._chunk_repo = chunk_repo

    async def retrieve(self, query: str, project_id: str, top_k: int = 3) -> RetrievalOutput:
        logger.info({"message": f"检索策略=PgBm25Retriever, project_id={project_id}, top_k={top_k}, query={query[:50]}"})
        timings: dict[str, int] = {}

        with measure(timings, "search"):
            search_results = await self._chunk_repo.search_fulltext(project_id, query, top_k)

        results = [
            RetrievalResult(chunk_id=r.chunk_id, score=r.score)
            for r in search_results
        ]

        return RetrievalOutput(
            results=results,
            embed_latency_ms=0,
            search_latency_ms=timings.get("search", 0),
        )
