from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class DocumentStatus(StrEnum):
    """文档状态枚举"""
    UPLOADED = "uploaded"
    CHUNKING = "chunking"
    CHUNKED = "chunked"
    EMBEDDING = "embedding"
    EMBEDDED = "embedded"
    READY = "ready"
    ERROR = "error"


# 允许触发处理的状态集合
_PROCESSABLE_STATUSES = frozenset({
    DocumentStatus.UPLOADED, DocumentStatus.ERROR,
    DocumentStatus.CHUNKING, DocumentStatus.EMBEDDING,
})

_TEXT_FILE_TYPES = frozenset({"md", "txt"})


@dataclass
class SplitterConfig:
    """分块配置值对象"""
    strategy: str = "section_heading"
    chunk_size: int = 500
    chunk_overlap: int = 50
    min_chars: int = 200
    max_chars: int = 2000

    def to_splitter_kwargs(self) -> dict:
        """根据策略构建分块器参数 — 纯函数，SplitterConfig 自己的事"""
        if self.strategy == "fixed":
            return {"chunk_size": self.chunk_size, "overlap": self.chunk_overlap}
        if self.strategy == "section_heading":
            return {"min_chars": self.min_chars, "max_chars": self.max_chars}
        return {}


@dataclass
class Document:
    """文档实体 — 上传的文件记录

    充血模型：封装永远成立的约束和纯函数性质的业务规则。
    业务场景的流程、需要外部信息的决策留在 Use Case。
    """

    id: str = ""
    project_id: str = ""
    filename: str = ""
    storage_key: str = ""
    file_size: int = 0
    file_type: str = ""
    checksum: str = ""
    status: DocumentStatus = DocumentStatus.UPLOADED
    splitter_config: SplitterConfig = field(default_factory=SplitterConfig)
    chunk_count: int = 0
    error_message: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None

    # ── 永远成立的约束 ────────────────────────────────────

    @property
    def can_process(self) -> bool:
        """当前状态是否允许触发处理"""
        return self.status in _PROCESSABLE_STATUSES

    @property
    def is_text_file(self) -> bool:
        """是否为文本类型文件（可预览源文件内容）"""
        return self.file_type in _TEXT_FILE_TYPES

    # ── 状态流转 — 保护不变量 ──────────────────────────────

    def start_chunking(self) -> None:
        """开始分块"""
        if not self.can_process:
            raise ValueError(f"文档状态不允许处理: {self.status}，仅 uploaded / error / chunking / embedding 可处理")
        self.status = DocumentStatus.CHUNKING

    def finish_chunking(self, chunk_count: int) -> None:
        """分块完成"""
        if self.status != DocumentStatus.CHUNKING:
            raise ValueError(f"当前状态 {self.status} 不允许完成分块")
        self.status = DocumentStatus.CHUNKED
        self.chunk_count = chunk_count

    def start_embedding(self) -> None:
        """开始嵌入"""
        if self.status != DocumentStatus.CHUNKED:
            raise ValueError(f"当前状态 {self.status} 不允许开始嵌入")
        self.status = DocumentStatus.EMBEDDING

    def finish_embedding(self) -> None:
        """嵌入完成"""
        if self.status != DocumentStatus.EMBEDDING:
            raise ValueError(f"当前状态 {self.status} 不允许完成嵌入")
        self.status = DocumentStatus.EMBEDDED

    def mark_ready(self) -> None:
        """标记就绪"""
        if self.status != DocumentStatus.EMBEDDED:
            raise ValueError(f"当前状态 {self.status} 不允许标记就绪")
        self.status = DocumentStatus.READY

    def mark_error(self, message: str) -> None:
        """标记错误"""
        self.status = DocumentStatus.ERROR
        self.error_message = message
