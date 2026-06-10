from abc import ABC, abstractmethod
from dataclasses import dataclass

from rag.domain.entities.embedding import Embedding


@dataclass
class EmbeddingSearchResult:
    """向量检索结果项"""

    chunk_id: str
    score: float


class EmbeddingRepositoryPort(ABC):
    """嵌入仓储端口 — 向量嵌入的持久化抽象"""

    @abstractmethod
    async def save_batch(self, embeddings: list[Embedding]) -> None: ...

    @abstractmethod
    async def get_by_chunk_id(self, chunk_id: str) -> Embedding | None: ...

    @abstractmethod
    async def list_by_project(self, project_id: str) -> list[Embedding]: ...

    @abstractmethod
    async def search_by_project(
        self, project_id: str, query_vector: list[float], top_k: int
    ) -> list[EmbeddingSearchResult]: ...
