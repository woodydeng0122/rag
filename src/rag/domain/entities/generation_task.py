from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class GenerationTask:
    """LLM 生成任务实体 — 追踪生成进度"""

    id: str = ""
    project_id: str = ""
    status: str = "running"
    total: int = 0
    completed: int = 0
    failed: int = 0
    document_ids: list[str] = field(default_factory=list)
    chunk_ids: list[str] = field(default_factory=list)
    config: dict = field(default_factory=dict)
    error_message: str = ""
    created_at: datetime | None = None
    finished_at: datetime | None = None
