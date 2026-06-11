import asyncio

from rag.domain.value_objects.retrieval_result import RetrievalResult
from rag.domain.value_objects.retrieval_output import RetrievalOutput
from rag.domain.ports.embedder_pool import EmbedderPoolPort
from rag.domain.ports.embedding_repository import EmbeddingRepositoryPort
from rag.domain.ports.embed_model_repository import EmbedModelRepositoryPort
from rag.domain.ports.project_repository import ProjectRepositoryPort
from rag.domain.ports.retriever import RetrieverPort
from rag.shared.logger import logger
from rag.shared.timer import measure


class VectorRetriever(RetrieverPort):
    """基于 pgvector 余弦相似度的检索器实现"""

    def __init__(
        self,
        embedder_pool: EmbedderPoolPort,
        embedding_repo: EmbeddingRepositoryPort,
        embed_model_repo: EmbedModelRepositoryPort,
        project_repo: ProjectRepositoryPort,
    ):
        self._embedder_pool = embedder_pool
        self._embedding_repo = embedding_repo
        self._embed_model_repo = embed_model_repo
        self._project_repo = project_repo

    async def retrieve(self, query: str, project_id: str, top_k: int = 3) -> RetrievalOutput:
        logger.info({"message": f"检索策略=VectorRetriever, project_id={project_id}, top_k={top_k}, query={query[:50]}"})
        timings: dict[str, int] = {}

        # 获取项目关联的嵌入模型
        embedder_model_name = ""
        with measure(timings, "load_project"):
            project = await self._project_repo.get_by_id(project_id)
        if project and project.embed_model_id:
            with measure(timings, "load_embed_model"):
                embed_model = await self._embed_model_repo.get_by_id(project.embed_model_id)
            if embed_model and embed_model.is_online:
                embedder_model_name = embed_model.name

        if not embedder_model_name:
            return RetrievalOutput(results=[], embed_latency_ms=0, search_latency_ms=0)

        # 获取对应的 embedder
        with measure(timings, "get_embedder"):
            embedder = self._embedder_pool.get(embedder_model_name)

        # 嵌入查询文本
        with measure(timings, "embed"):
            query_vectors = await asyncio.to_thread(embedder.embed, query)
            query_vector = query_vectors[0]

        # pgvector 向量检索
        with measure(timings, "search"):
            search_results = await self._embedding_repo.search_by_project(
                project_id, query_vector, top_k
            )

        results = [
            RetrievalResult(chunk_id=r.chunk_id, score=r.score)
            for r in search_results
        ]

        return RetrievalOutput(
            results=results,
            embed_latency_ms=timings.get("embed", 0),
            search_latency_ms=timings.get("search", 0),
            load_project_latency_ms=timings.get("load_project", 0),
            load_embed_model_latency_ms=timings.get("load_embed_model", 0),
            get_embedder_latency_ms=timings.get("get_embedder", 0),
        )
