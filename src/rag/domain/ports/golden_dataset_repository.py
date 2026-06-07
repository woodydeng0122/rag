from abc import ABC, abstractmethod

from rag.domain.entities.golden_record import GoldenRecord, GoldenStatus


class GoldenDatasetRepositoryPort(ABC):
    """黄金数据集仓储端口 — 黄金记录持久化的抽象"""

    @abstractmethod
    async def save(self, record: GoldenRecord) -> GoldenRecord: ...

    @abstractmethod
    async def get_by_id(self, record_id: str) -> GoldenRecord | None: ...

    @abstractmethod
    async def list_by_project(self, project_id: str) -> list[GoldenRecord]: ...

    @abstractmethod
    async def update(self, record: GoldenRecord) -> GoldenRecord: ...

    @abstractmethod
    async def delete(self, record_id: str) -> bool: ...

    @abstractmethod
    async def list_by_project_and_status(
        self, project_id: str, status: GoldenStatus
    ) -> list[GoldenRecord]: ...

    @abstractmethod
    async def update_status(self, record_id: str, status: GoldenStatus) -> GoldenRecord: ...

    @abstractmethod
    async def batch_update_status(self, record_ids: list[str], status: GoldenStatus) -> int: ...

    @abstractmethod
    async def list_by_chunk_id(self, chunk_id: str, project_id: str) -> list[GoldenRecord]: ...

    @abstractmethod
    async def count_by_document_ids(self, document_ids: list[str]) -> dict[str, int]: ...

    @abstractmethod
    async def list_by_document(self, project_id: str, document_id: str) -> list[GoldenRecord]: ...
