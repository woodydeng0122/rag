from enum import Enum

from pydantic import BaseModel, Field


class GoldenStatusEnum(str, Enum):
    """API 层黄金记录状态枚举 — 与领域层解耦"""

    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class CreateGoldenRequest(BaseModel):
    query: str = Field(..., description="查询文本")
    ground_truth_chunks: list[str] = Field(..., description="关联的真实分块 ID 列表")
    reference_answer: str = Field("", description="参考答案")


class UpdateGoldenRequest(BaseModel):
    query: str | None = Field(None, description="查询文本")
    ground_truth_chunks: list[str] | None = Field(None, description="关联的真实分块 ID 列表")
    reference_answer: str | None = Field(None, description="参考答案")
    status: GoldenStatusEnum | None = Field(None, description="状态")


class EvaluationMetricsResponse(BaseModel):
    retrieved_chunk_ids: list[str] = Field(default_factory=list)
    is_hit: bool | None = None
    hit_rank: int | None = None
    evaluated_at: str | None = None


class GoldenResponse(BaseModel):
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


class ImportGoldenResponse(BaseModel):
    success_count: int = 0
    skipped_count: int = 0
    skipped: list[SkippedRecordResponse] = Field(default_factory=list)


class BatchStatusUpdateRequest(BaseModel):
    record_ids: list[str] = Field(..., description="记录 ID 列表")


class BatchStatusUpdateResponse(BaseModel):
    updated_count: int
