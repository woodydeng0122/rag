from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from rag.domain.value_objects.generate_config import GenerateConfig


class TaskStatus(str, Enum):
    """生成任务状态枚举 — 避免魔法字符串"""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class GenerationTask:
    """LLM 生成任务实体 — 追踪生成进度"""

    id: str = ""
    project_id: str = ""
    status: TaskStatus = TaskStatus.RUNNING
    total: int = 0
    completed: int = 0
    failed: int = 0
    document_ids: list[str] = field(default_factory=list)
    chunk_ids: list[str] = field(default_factory=list)
    config: GenerateConfig | None = None
    error_message: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
    finished_at: datetime | None = None

    def complete(self) -> None:
        """标记任务完成"""
        if self.status != TaskStatus.RUNNING:
            raise ValueError(f"Cannot complete task in status {self.status}")
        self.status = TaskStatus.COMPLETED
        self.finished_at = datetime.now()

    def fail(self, error_message: str = "") -> None:
        """标记任务失败"""
        if self.status != TaskStatus.RUNNING:
            raise ValueError(f"Cannot fail task in status {self.status}")
        self.status = TaskStatus.FAILED
        self.error_message = error_message[:500]
        self.finished_at = datetime.now()

    def increment_completed(self, count: int = 1) -> None:
        """递增已完成计数"""
        self.completed += count

    def increment_failed(self, count: int = 1) -> None:
        """递增失败计数"""
        self.failed += count
