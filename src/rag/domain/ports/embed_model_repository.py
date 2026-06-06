from abc import ABC, abstractmethod

from rag.domain.entities.embed_model import EmbedModel, ModelConfig, ModelStatus


class EmbedModelRepositoryPort(ABC):
    """嵌入模型仓储端口 — 模型注册信息的持久化抽象"""

    @abstractmethod
    async def save(self, model: EmbedModel) -> EmbedModel: ...

    @abstractmethod
    async def save_batch(self, models: list[EmbedModel]) -> list[EmbedModel]: ...

    @abstractmethod
    async def get_all(self) -> list[EmbedModel]: ...

    @abstractmethod
    async def get_by_id(self, model_id: str) -> EmbedModel | None: ...

    @abstractmethod
    async def get_by_name(self, name: str) -> EmbedModel | None: ...

    @abstractmethod
    async def update(self, model: EmbedModel) -> EmbedModel: ...

    @abstractmethod
    async def delete(self, model_id: str) -> bool: ...
