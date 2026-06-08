from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class GoldenStatus(str, Enum):
    """黄金记录状态枚举 — 避免魔法字符串"""

    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class GoldenRecord:
    """评测黄金记录实体 — 含查询、真实分块、参考答案

    充血模型：封装永远成立的约束和纯函数性质的业务规则。
    业务场景的流程、需要外部信息的决策留在 Use Case。
    """

    query: str
    ground_truth_chunks: list[str] = field(default_factory=list)
    reference_answer: str = ""
    id: str = ""
    project_id: str = ""
    status: GoldenStatus = GoldenStatus.APPROVED
    created_at: datetime | None = None
    updated_at: datetime | None = None
    metadata: dict = field(default_factory=dict)

    # ── 修改规则 ──────────────────────────────────────────

    def update_content(self, query: str, ground_truth_chunks: list[str], reference_answer: str) -> None:
        """更新黄金记录内容 — 封装内容修改规则"""
        self.query = query
        self.ground_truth_chunks = ground_truth_chunks
        self.reference_answer = reference_answer

    # ── 状态流转 — 保护不变量 ──────────────────────────────

    def approve(self) -> None:
        """审批通过"""
        self.status = GoldenStatus.APPROVED

    def reject(self) -> None:
        """拒绝"""
        self.status = GoldenStatus.REJECTED
