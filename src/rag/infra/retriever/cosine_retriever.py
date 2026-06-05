import numpy as np
from rag.domain.entities.embedding import Embedding
from rag.domain.entities.retrieval_result import RetrievalResult
from rag.domain.ports.embedder import EmbedderPort
from rag.domain.ports.embedding_repository import EmbeddingRepositoryPort
from rag.domain.ports.retriever import RetrieverPort


class CosineRetriever(RetrieverPort):
    """基于余弦相似度的检索器实现"""

    def __init__(
        self,
        embedder: EmbedderPort,
        embedding_repo: EmbeddingRepositoryPort,
        embedding_file: str,
    ):
        self._embedder = embedder
        self._embedding_repo = embedding_repo
        self._embedding_file = embedding_file

    def retrieve(self, query: str, top_k: int = 3) -> list[RetrievalResult]:
        # 加载嵌入
        embeddings = self._embedding_repo.load(self._embedding_file)
        if not embeddings:
            return []

        # 构建嵌入矩阵
        embeddings_array = np.array([e.vector for e in embeddings])

        # 查询嵌入
        query_vectors = self._embedder.embed(query)
        query_emb = np.array(query_vectors[0])

        # 计算余弦相似度
        scores = np.dot(embeddings_array, query_emb)
        sorted_indices = scores.argsort()
        best_indices = sorted_indices[-top_k:][::-1]

        return [
            RetrievalResult(chunk_id=embeddings[i].chunk_id, score=float(scores[i]))
            for i in best_indices
        ]
