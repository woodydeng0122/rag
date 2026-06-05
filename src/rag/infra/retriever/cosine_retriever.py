import numpy as np
from rag.domain.entities.retrieval_result import RetrievalResult
from rag.domain.ports.embedder_pool import EmbedderPoolPort
from rag.domain.ports.embedding_repository import EmbeddingRepositoryPort
from rag.domain.ports.embed_model_repository import EmbedModelRepositoryPort
from rag.domain.ports.retriever import RetrieverPort


class CosineRetriever(RetrieverPort):
    """基于余弦相似度的检索器实现"""

    def __init__(
        self,
        embedder_pool: EmbedderPoolPort,
        embedding_repo: EmbeddingRepositoryPort,
        embed_model_repo: EmbedModelRepositoryPort,
    ):
        self._embedder_pool = embedder_pool
        self._embedding_repo = embedding_repo
        self._embed_model_repo = embed_model_repo

    async def retrieve(self, query: str, project_id: str, top_k: int = 3) -> list[RetrievalResult]:
        # 从 PG 按项目加载嵌入
        embeddings = await self._embedding_repo.list_by_project(project_id)
        if not embeddings:
            return []

        # 获取项目关联的嵌入模型名（用于选择正确的 embedder）
        # 从第一条嵌入记录获取 embedder_model 字段
        embedder_model_name = ""
        if embeddings:
            # 尝试从 embedding 表获取模型名
            pool = self._embedding_repo
            # 简化：使用 embed_model_repo 查找所有在线模型，取第一个
            # TODO: 后续可通过 project 表的 embed_model_id 精确查找
            models = await self._embed_model_repo.get_all()
            online_models = [m for m in models if m.status == "online"]
            if online_models:
                embedder_model_name = online_models[0].name

        if not embedder_model_name:
            return []

        # 获取对应的 embedder
        embedder = self._embedder_pool.get(embedder_model_name)

        # 构建嵌入矩阵
        embeddings_array = np.array([e.vector for e in embeddings])

        # 查询嵌入
        query_vectors = embedder.embed(query)
        query_emb = np.array(query_vectors[0])

        # 计算余弦相似度
        scores = np.dot(embeddings_array, query_emb)
        sorted_indices = scores.argsort()
        best_indices = sorted_indices[-top_k:][::-1]

        return [
            RetrievalResult(chunk_id=embeddings[i].chunk_id, score=float(scores[i]))
            for i in best_indices
        ]
