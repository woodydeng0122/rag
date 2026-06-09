from dataclasses import dataclass, field


@dataclass
class QASession:
    """问答会话实体"""

    id: str
    project_id: str
    title: str
    created_at: str
    updated_at: str

    def update_title(self, title: str) -> None:
        self.title = title


@dataclass
class QAMessageChunk:
    """消息中引用的检索分块"""

    chunk_id: str
    content: str
    score: float
    source_file: str
    heading: str


@dataclass
class QAMessage:
    """问答消息实体"""

    id: str
    session_id: str
    role: str  # 'user' | 'assistant'
    content: str
    chunks: list[QAMessageChunk] = field(default_factory=list)
    latency_ms: int | None = None
    created_at: str = ""
