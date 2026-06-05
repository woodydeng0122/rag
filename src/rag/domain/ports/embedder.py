from abc import ABC, abstractmethod


class EmbedderPort(ABC):
    """嵌入器端口 — 文本转向量的抽象"""

    @abstractmethod
    def embed(self, text: str | list[str]) -> list[list[float]]: ...
