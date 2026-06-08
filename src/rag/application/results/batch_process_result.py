from dataclasses import dataclass

from rag.domain.entities.chunk import Chunk
from rag.domain.entities.document import Document


@dataclass
class ChunksWithDoc:
    """分块列表 + 所属文档信息"""

    chunks: list[Chunk]
    document_id: str
    file_type: str


@dataclass
class SourceContentWithDoc:
    """源文件内容 + 所属文档信息"""

    content: str
    document_id: str
    file_type: str


@dataclass
class BatchProcessResult:
    """批量处理结果"""

    total: int
    success: int
    failed: int
    results: list[BatchProcessItem]


@dataclass
class BatchProcessItem:
    """批量处理单项结果"""

    id: str
    status: str
    chunk_count: int = 0
    error_message: str = ""
