from dataclasses import dataclass


@dataclass
class Chunk:
    """文档分块实体 — RAG 系统的最基本单元

    充血模型：封装永远成立的约束和纯函数性质的业务规则。
    业务场景的流程、需要外部信息的决策留在 Use Case。
    """

    id: str
    content: str
    index: int = 0
    source_file: str = ""
    heading: str = ""

    # ── 永远成立的约束 ────────────────────────────────────

    def ensure_valid(self) -> None:
        """校验分块完整性 — 内容不能为空，任何场景都应遵守"""
        if not self.content.strip():
            raise ValueError("分块内容不能为空")

    # ── 纯函数性质的业务规则 ──────────────────────────────

    def assign_identity(self, document_id: str, index: int, source_file: str) -> None:
        """分配分块身份 — 封装 ID 生成规则，纯函数无副作用"""
        self.id = f"{document_id}_chunk_{index}"
        self.index = index
        self.source_file = source_file
