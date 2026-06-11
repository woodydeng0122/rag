from abc import ABC, abstractmethod
from rag.domain.entities.chunk import Chunk
from rag.domain.value_objects.fulltext_search_result import FulltextSearchResult


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

    @abstractmethod
    async def get_by_ids_with_file_type(self, chunk_ids: list[str]) -> list[tuple[Chunk, str]]:
        """按 ID 列表批量查询 chunk，同时返回所属文档的 file_type"""
        ...

    @abstractmethod
    async def count_by_project(self, project_id: str) -> int:
        """统计项目下的分块总数"""
        ...

    @abstractmethod
    async def search_fulltext(self, project_id: str, query: str, top_k: int = 10) -> list[FulltextSearchResult]:
        """全文检索 — 基于 ts_vector 的 BM25 风格搜索"""
        ...
