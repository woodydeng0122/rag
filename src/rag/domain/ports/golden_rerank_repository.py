from abc import ABC, abstractmethod
from dataclasses import dataclass

from rag.domain.entities.golden_rerank import GoldenRerank
from rag.domain.entities.golden_rerank_item import GoldenRerankItem


@dataclass
class RerankSummary:
    """重排命中摘要"""

    hit_count: int
    gt_total: int
    hit_ranks: list[int]


class GoldenRerankRepositoryPort(ABC):
    """黄金记录重排结果仓储端口"""

    @abstractmethod
    async def save(self, rerank: GoldenRerank, items: list[GoldenRerankItem]) -> GoldenRerank:
        """保存重排结果（含明细），覆盖该 golden_id 的旧结果"""
        ...

    @abstractmethod
    async def get_by_golden_id(self, golden_id: str) -> tuple[GoldenRerank, list[GoldenRerankItem]] | None:
        """按 golden_id 获取重排结果及明细"""
        ...

    @abstractmethod
    async def delete_by_golden_id(self, golden_id: str) -> bool:
        """按 golden_id 删除重排结果（CASCADE 删明细）"""
        ...

    @abstractmethod
    async def exists_by_golden_ids(self, golden_ids: list[str]) -> set[str]:
        """批量判断哪些 golden_id 存在重排结果，返回有结果的 ID 集合"""
        ...

    @abstractmethod
    async def get_rerank_summaries(self, golden_ids: list[str]) -> dict[str, RerankSummary]:
        """批量获取重排命中摘要 — hit_count 为 GT 命中数，gt_total 为 GT 总数"""
        ...
