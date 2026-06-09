from dataclasses import dataclass, field


@dataclass
class QASessionResult:
    """会话列表项"""
    id: str
    project_id: str
    title: str
    created_at: str
    updated_at: str


@dataclass
class QAMessageChunkResult:
    """消息引用的分块"""
    chunk_id: str
    content: str
    score: float
    source_file: str
    heading: str


@dataclass
class QAMessageResult:
    """消息结果"""
    id: str
    session_id: str
    role: str
    content: str
    chunks: list[QAMessageChunkResult] = field(default_factory=list)
    latency_ms: int | None = None
    created_at: str = ""


@dataclass
class AskStreamEvent:
    """SSE 流式事件"""
    type: str  # 'chunk' | 'sources' | 'done' | 'error'
    data: str = ""
    chunks: list[QAMessageChunkResult] = field(default_factory=list)
    latency_ms: int | None = None
