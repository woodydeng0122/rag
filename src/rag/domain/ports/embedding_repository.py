from abc import ABC, abstractmethod
from rag.domain.entities.embedding import Embedding


class EmbeddingRepositoryPort(ABC):
    """嵌入仓储端口 — 向量嵌入的持久化抽象"""

    @abstractmethod
    def save(self, embeddings: list[Embedding], filepath: str) -> None: ...

    @abstractmethod
    def load(self, filepath: str) -> list[Embedding]: ...

    @abstractmethod
    async def save_batch(self, embeddings: list[Embedding], embedder_model: str = "") -> None: ...

    @abstractmethod
    async def get_by_chunk_id(self, chunk_id: str) -> Embedding | None: ...
