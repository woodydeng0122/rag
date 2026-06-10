from abc import ABC, abstractmethod
from rag.domain.entities.project import Project


class ProjectRepositoryPort(ABC):
    """项目仓储端口 — 项目持久化的抽象"""

    @abstractmethod
    async def save(self, project: Project) -> Project: ...

    @abstractmethod
    async def get_by_id(self, project_id: str) -> Project | None: ...

    @abstractmethod
    async def get_by_name(self, name: str) -> Project | None: ...

    @abstractmethod
    async def list(self, user_id: str | None = None) -> list[Project]: ...

    @abstractmethod
    async def update(self, project: Project) -> Project: ...

    @abstractmethod
    async def delete(self, project_id: str) -> bool: ...
