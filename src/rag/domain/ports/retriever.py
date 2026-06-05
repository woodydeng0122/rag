from abc import ABC, abstractmethod
from rag.domain.entities.retrieval_result import RetrievalResult


class RetrieverPort(ABC):
    """检索器端口 — 根据查询检索相关分块的抽象"""

    @abstractmethod
    async def retrieve(self, query: str, project_id: str, top_k: int = 3) -> list[RetrievalResult]: ...
