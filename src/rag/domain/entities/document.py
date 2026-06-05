from dataclasses import dataclass
from datetime import datetime


@dataclass
class Document:
    """文档实体 — 上传的文件记录"""
    id: str = ""
    project_id: str = ""
    filename: str = ""
    file_path: str = ""
    file_size: int = 0
    file_type: str = ""
    checksum: str = ""
    status: str = "uploaded"
    embedder_model: str = ""
    splitter_strategy: str = "section_heading"
    chunk_size: int = 500
    chunk_overlap: int = 50
    splitter_min_chars: int = 200
    splitter_max_chars: int = 2000
    chunk_count: int = 0
    error_message: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
