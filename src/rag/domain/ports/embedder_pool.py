from abc import ABC, abstractmethod

from rag.domain.ports.embedder import EmbedderPort


class EmbedderPoolPort(ABC):
    """Embedder 实例缓存池端口 — 按模型名获取 embedder 的抽象"""

    @abstractmethod
    def get(self, model_name: str) -> EmbedderPort: ...

    @abstractmethod
    def is_loaded(self, model_name: str) -> bool: ...

    @abstractmethod
    def loaded_models(self) -> list[str]: ...
