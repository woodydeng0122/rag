import asyncio
import time

import numpy as np
from rag.domain.value_objects.retrieval_result import RetrievalResult
from rag.domain.value_objects.retrieval_output import RetrievalOutput
from rag.domain.ports.embedder_pool import EmbedderPoolPort
from rag.domain.ports.embedding_repository import EmbeddingRepositoryPort
from rag.domain.ports.embed_model_repository import EmbedModelRepositoryPort
from rag.domain.ports.project_repository import ProjectRepositoryPort
from rag.domain.ports.retriever import RetrieverPort


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
        # 从 PG 按项目加载嵌入
        embeddings = await self._embedding_repo.list_by_project(project_id)
        if not embeddings:
            return RetrievalOutput(results=[], embed_latency_ms=0, search_latency_ms=0)

        # 获取项目关联的嵌入模型
        embedder_model_name = ""
        project = await self._project_repo.get_by_id(project_id)
        if project and project.embed_model_id:
            embed_model = await self._embed_model_repo.get_by_id(project.embed_model_id)
            if embed_model and embed_model.is_online:
                embedder_model_name = embed_model.name

        if not embedder_model_name:
            return RetrievalOutput(results=[], embed_latency_ms=0, search_latency_ms=0)

        # 获取对应的 embedder
        embedder = self._embedder_pool.get(embedder_model_name)

        # 构建嵌入矩阵
        embeddings_array = np.array([e.vector for e in embeddings])

        # 计时: 嵌入
        embed_start = time.monotonic()
        query_vectors = await asyncio.to_thread(embedder.embed, query)
        query_emb = np.array(query_vectors[0])
        embed_latency_ms = int((time.monotonic() - embed_start) * 1000)

        # 计时: 检索（含 DB 加载 + 向量计算）
        search_start = time.monotonic()
        scores = np.dot(embeddings_array, query_emb)
        sorted_indices = scores.argsort()
        best_indices = sorted_indices[-top_k:][::-1]
        search_latency_ms = int((time.monotonic() - search_start) * 1000)

        results = [
            RetrievalResult(chunk_id=embeddings[i].chunk_id, score=float(scores[i]))
            for i in best_indices
        ]

        return RetrievalOutput(
            results=results,
            embed_latency_ms=embed_latency_ms,
            search_latency_ms=search_latency_ms,
        )
