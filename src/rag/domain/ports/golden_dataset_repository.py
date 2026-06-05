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
