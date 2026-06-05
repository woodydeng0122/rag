from abc import ABC, abstractmethod
from rag.domain.entities.chunk import Chunk


class ChunkRepositoryPort(ABC):
    """分块仓储端口 — 分块的持久化抽象"""

    @abstractmethod
    def save(self, chunks: list[Chunk], filepath: str) -> None: ...

    @abstractmethod
    def load(self, filepath: str) -> list[Chunk]: ...

    @abstractmethod
    async def save_batch(self, chunks: list[Chunk], document_id: str = "") -> None: ...

    @abstractmethod
    async def list_by_document(self, document_id: str) -> list[Chunk]: ...
