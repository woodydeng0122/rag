from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class GoldenRecord:
    """评测黄金记录实体 — 含查询、真实分块、参考答案、评测结果"""

    query: str
    ground_truth_chunks: list[str] = field(default_factory=list)
    reference_answer: str = ""
    id: str = ""
    project_id: str = ""
    retrieved_chunk_ids: list[str] = field(default_factory=list)
    is_hit: bool | None = None
    hit_rank: int | None = None
    evaluated_at: datetime | None = None
    created_at: datetime | None = None
    metadata: dict = field(default_factory=dict)

    def set_retrieved(self, ids: list[str]) -> None:
        """设置检索结果 ID 列表"""
        self.retrieved_chunk_ids = ids

    @property
    def retrieved_ids(self) -> list[str]:
        """获取检索结果 ID 列表"""
        return self.retrieved_chunk_ids
