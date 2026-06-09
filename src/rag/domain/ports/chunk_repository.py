from abc import ABC, abstractmethod
from rag.domain.entities.chunk import Chunk


class ChunkRepositoryPort(ABC):
    """分块仓储端口 — 分块的持久化抽象"""

    @abstractmethod
    async def save_batch(self, chunks: list[Chunk], document_id: str = "") -> None: ...

    @abstractmethod
    async def list_by_document(self, document_id: str) -> list[Chunk]: ...

    @abstractmethod
    async def list_by_project(self, project_id: str, limit: int = 20, offset: int = 0) -> list[Chunk]: ...

    @abstractmethod
    async def search_by_project(self, project_id: str, query: str, limit: int = 20, offset: int = 0) -> list[Chunk]: ...

    @abstractmethod
    async def get_by_ids(self, chunk_ids: list[str]) -> list[Chunk]:
        """按 ID 列表批量查询 chunk"""
        ...
