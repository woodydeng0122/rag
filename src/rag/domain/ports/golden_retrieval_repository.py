from abc import ABC, abstractmethod

from rag.domain.entities.golden_retrieval import GoldenRetrieval
from rag.domain.entities.golden_retrieval_item import GoldenRetrievalItem


class GoldenRetrievalRepositoryPort(ABC):
    """黄金记录检索结果仓储端口"""

    @abstractmethod
    async def save(self, retrieval: GoldenRetrieval, items: list[GoldenRetrievalItem]) -> GoldenRetrieval:
        """保存检索结果（含明细），覆盖该 golden_id 的旧结果"""
        ...

    @abstractmethod
    async def get_by_golden_id(self, golden_id: str) -> tuple[GoldenRetrieval, list[GoldenRetrievalItem]] | None:
        """按 golden_id 获取检索结果及明细"""
        ...

    @abstractmethod
    async def delete_by_golden_id(self, golden_id: str) -> bool:
        """按 golden_id 删除检索结果（CASCADE 删明细）"""
        ...

    @abstractmethod
    async def exists_by_golden_id(self, golden_id: str) -> bool:
        """判断 golden_id 是否存在检索结果"""
        ...

    @abstractmethod
    async def exists_by_golden_ids(self, golden_ids: list[str]) -> set[str]:
        """批量判断哪些 golden_id 存在检索结果，返回有结果的 ID 集合"""
        ...
