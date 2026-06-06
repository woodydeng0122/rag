from abc import ABC, abstractmethod
from rag.domain.entities.golden_record import GoldenRecord


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
        self, project_id: str, status: str
    ) -> list[GoldenRecord]: ...

    @abstractmethod
    async def update_status(self, record_id: str, status: str) -> GoldenRecord: ...

    @abstractmethod
    async def batch_update_status(self, record_ids: list[str], status: str) -> int: ...

    @abstractmethod
    async def list_by_chunk_id(self, chunk_id: str, project_id: str) -> list[GoldenRecord]: ...
