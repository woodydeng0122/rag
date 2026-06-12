from abc import ABC, abstractmethod

from rag.domain.value_objects.rerank_result import RerankResult


class RerankerPort(ABC):
    """重排器端口 — 对候选文档进行 cross-encoder 精排的抽象"""

    @abstractmethod
    async def rerank(self, query: str, documents: list[str], top_k: int = 10) -> list[RerankResult]: ...


class RerankerPoolPort(ABC):
    """重排器池端口 — 按 model_path 获取 CrossEncoder 实例的抽象"""

    @abstractmethod
    def get(self, model_path: str):
        """获取或创建 CrossEncoder 实例"""
        ...
