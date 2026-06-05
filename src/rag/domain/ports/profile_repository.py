from abc import ABC, abstractmethod

from rag.domain.entities.profile import Profile


class ProfileRepositoryPort(ABC):
    """用户配置仓储端口 — profile 持久化的抽象"""

    @abstractmethod
    async def get(self) -> Profile: ...

    @abstractmethod
    async def upsert(self, active_project_id: str | None) -> Profile: ...
