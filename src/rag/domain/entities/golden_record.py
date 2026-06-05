from dataclasses import dataclass, field


@dataclass
class GoldenRecord:
    """评测黄金记录实体 — 含查询、真实分块、参考答案"""

    query: str
    ground_truth_chunks: list[str]
    reference_answer: str = ""
    _retrieved_ids: list[str] = field(default_factory=list)

    def set_retrieved(self, ids: list[str]) -> None:
        """设置检索结果 ID 列表"""
        self._retrieved_ids = ids

    @property
    def retrieved_ids(self) -> list[str]:
        """获取检索结果 ID 列表"""
        return self._retrieved_ids
