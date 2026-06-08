from enum import Enum

from pydantic import BaseModel, Field


class GoldenStatusEnum(str, Enum):
    """API 层黄金记录状态枚举 — 与领域层解耦"""

    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class TaskStatusEnum(str, Enum):
    """API 层生成任务状态枚举 — 与领域层解耦"""

    RUNNING = "running"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"


class CreateGoldenDatasetRequest(BaseModel):
    query: str = Field(..., description="查询文本")
    ground_truth_chunks: list[str] = Field(..., description="关联的真实分块 ID 列表")
    reference_answer: str = Field("", description="参考答案")


class UpdateGoldenDatasetRequest(BaseModel):
    query: str | None = Field(None, description="查询文本")
    ground_truth_chunks: list[str] | None = Field(None, description="关联的真实分块 ID 列表")
    reference_answer: str | None = Field(None, description="参考答案")
    status: GoldenStatusEnum | None = Field(None, description="状态")


class EvaluationMetricsResponse(BaseModel):
    retrieved_chunk_ids: list[str] = Field(default_factory=list)
    is_hit: bool | None = None
    hit_rank: int | None = None
    evaluated_at: str | None = None


class GoldenDatasetResponse(BaseModel):
    id: str
    project_id: str
    query: str
    ground_truth_chunks: list[str]
    reference_answer: str = ""
    status: GoldenStatusEnum = GoldenStatusEnum.APPROVED
    evaluation: EvaluationMetricsResponse | None = None
    created_at: str = ""
    metadata: dict = Field(default_factory=dict)


class SkippedRecordResponse(BaseModel):
    row: int
    reason: str


class ImportGoldenDatasetResponse(BaseModel):
    success_count: int = 0
    skipped_count: int = 0
    skipped: list[SkippedRecordResponse] = Field(default_factory=list)


# --- 生成相关 ---

class GenerateConfigSchema(BaseModel):
    per_chunk: int = Field(2, description="每 chunk 生成问题数")
    question_types: list[str] | dict[str, float] | None = Field(None, description="问题类型列表或类型及占比")
    difficulty: str = Field("mixed", description="难度: easy / medium / hard / mixed")
    user_persona: str = Field("开发者", description="用户群体描述")
    chunk_batch_size: int = Field(3, description="大文件每轮 chunk 数")
    file_char_threshold: int = Field(5000, description="文件字符数阈值")

    def resolve_question_types(self) -> dict[str, float] | None:
        """将 list[str] 均分转换为 dict[str, float]，dict 直接返回"""
        if self.question_types is None:
            return None
        if isinstance(self.question_types, dict):
            return self.question_types
        # list[str] → 均分占比
        count = len(self.question_types)
        if count == 0:
            return None
        share = round(1.0 / count, 4)
        return {t: share for t in self.question_types}


class GenerateGoldenRequest(BaseModel):
    document_ids: list[str] = Field(default_factory=list, description="选定文档 ID 列表")
    chunk_ids: list[str] = Field(default_factory=list, description="选定分块 ID 列表（优先于 document_ids）")
    config: GenerateConfigSchema | None = Field(None, description="生成配置")


class GenerateGoldenResponse(BaseModel):
    task_id: str
    status: TaskStatusEnum = TaskStatusEnum.RUNNING


class GenerationTaskResponse(BaseModel):
    id: str
    project_id: str
    status: TaskStatusEnum
    total: int = 0
    completed: int = 0
    failed: int = 0
    document_ids: list[str] = Field(default_factory=list)
    chunk_ids: list[str] = Field(default_factory=list)
    config: dict = Field(default_factory=dict)
    error_message: str = ""
    created_at: str = ""
    updated_at: str | None = None
    finished_at: str | None = None


class BatchStatusUpdateRequest(BaseModel):
    record_ids: list[str] = Field(..., description="记录 ID 列表")


class BatchStatusUpdateResponse(BaseModel):
    updated_count: int
