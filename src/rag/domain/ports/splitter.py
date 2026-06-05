from abc import ABC, abstractmethod
from rag.domain.entities.chunk import Chunk


class SplitterPort(ABC):
    """分块策略端口 — 文本分块的抽象"""

    @abstractmethod
    def split(self, text: str, **kwargs) -> list[Chunk]: ...
