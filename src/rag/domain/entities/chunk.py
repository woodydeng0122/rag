from dataclasses import dataclass, field


@dataclass
class Chunk:
    """文档分块实体 — RAG 系统的最基本单元"""
    id: str
    content: str
    index: int = 0
    source_file: str = ""
    heading: str = ""
