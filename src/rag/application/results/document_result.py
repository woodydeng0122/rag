from dataclasses import dataclass

from rag.domain.entities.document import Document


@dataclass
class DocumentWithGoldenCount:
    """文档 + 关联黄金记录数量"""

    document: Document
    golden_count: int = 0
