from abc import ABC, abstractmethod

from rag.domain.entities.generation_task import GenerationTask


class GenerationTaskRepositoryPort(ABC):
    """生成任务仓储端口 — 生成任务持久化的抽象"""

    @abstractmethod
    async def save(self, task: GenerationTask) -> GenerationTask: ...

    @abstractmethod
    async def get_by_id(self, task_id: str) -> GenerationTask | None: ...

    @abstractmethod
    async def list_by_project(self, project_id: str) -> list[GenerationTask]: ...

    @abstractmethod
    async def update(self, task: GenerationTask) -> GenerationTask: ...
