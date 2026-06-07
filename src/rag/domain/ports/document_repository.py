from abc import ABC, abstractmethod

from rag.domain.entities.document import Document, DocumentStatus


class DocumentRepositoryPort(ABC):
    """文档仓储端口 — 文档持久化的抽象"""

    @abstractmethod
    async def save(self, document: Document) -> Document: ...

    @abstractmethod
    async def get_by_id(self, document_id: str) -> Document | None: ...

    @abstractmethod
    async def list_by_project(self, project_id: str) -> list[Document]: ...

    @abstractmethod
    async def update_status(self, document_id: str, status: DocumentStatus, error_message: str = "") -> None: ...

    @abstractmethod
    async def update_chunk_count(self, document_id: str, chunk_count: int) -> None: ...

    @abstractmethod
    async def get_by_storage_key(self, storage_key: str) -> Document | None: ...

    @abstractmethod
    async def delete(self, document_id: str) -> bool: ...
