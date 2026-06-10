import asyncio

import numpy as np
from rag.domain.value_objects.retrieval_result import RetrievalResult
from rag.domain.value_objects.retrieval_output import RetrievalOutput
from rag.domain.ports.embedder_pool import EmbedderPoolPort
from rag.domain.ports.embedding_repository import EmbeddingRepositoryPort
from rag.domain.ports.embed_model_repository import EmbedModelRepositoryPort
from rag.domain.ports.project_repository import ProjectRepositoryPort
from rag.domain.ports.retriever import RetrieverPort
from rag.shared.timer import measure


class CosineRetriever(RetrieverPort):
    """基于余弦相似度的检索器实现"""

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
        timings: dict[str, int] = {}

        # 从 PG 按项目加载嵌入
        with measure(timings, "load_embeddings"):
            embeddings = await self._embedding_repo.list_by_project(project_id)
        if not embeddings:
            return RetrievalOutput(results=[], embed_latency_ms=0, search_latency_ms=0)

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

        # 构建嵌入矩阵
        with measure(timings, "build_matrix"):
            embeddings_array = np.array([e.vector for e in embeddings])

        with measure(timings, "embed"):
            query_vectors = await asyncio.to_thread(embedder.embed, query)
            query_emb = np.array(query_vectors[0])

        with measure(timings, "search"):
            scores = np.dot(embeddings_array, query_emb)
            sorted_indices = scores.argsort()
            best_indices = sorted_indices[-top_k:][::-1]

        results = [
            RetrievalResult(chunk_id=embeddings[i].chunk_id, score=float(scores[i]))
            for i in best_indices
        ]

        return RetrievalOutput(
            results=results,
            embed_latency_ms=timings.get("embed", 0),
            search_latency_ms=timings.get("search", 0),
            load_embeddings_latency_ms=timings.get("load_embeddings", 0),
            load_project_latency_ms=timings.get("load_project", 0),
            load_embed_model_latency_ms=timings.get("load_embed_model", 0),
            get_embedder_latency_ms=timings.get("get_embedder", 0),
            build_matrix_latency_ms=timings.get("build_matrix", 0),
        )
