from abc import ABC, abstractmethod

from rag.domain.value_objects.rerank_result import RerankResult


class RerankerPort(ABC):
    """重排器端口 — 对候选文档进行 cross-encoder 精排的抽象"""

    @abstractmethod
    async def rerank(self, query: str, documents: list[str], top_k: int = 10) -> list[RerankResult]: ...
