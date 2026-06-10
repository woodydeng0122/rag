from abc import ABC, abstractmethod

from rag.domain.entities.profile import Profile


class ProfileRepositoryPort(ABC):
    """用户配置仓储端口 — profile 持久化的抽象（per-user）"""

    @abstractmethod
    async def get(self, user_id: str) -> Profile: ...

    @abstractmethod
    async def upsert(self, user_id: str, active_project_id: str | None) -> Profile: ...
