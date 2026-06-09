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


class RetrievalSummaryResponse(BaseModel):
    hit_count: int = 0
    gt_total: int = 0


class GoldenResponse(BaseModel):
    id: str
    project_id: str
    query: str
    ground_truth_chunks: list[str]
    reference_answer: str = ""
    status: GoldenStatusEnum = GoldenStatusEnum.APPROVED
    created_at: str = ""
    metadata: dict = Field(default_factory=dict)
    has_retrieval: bool = False
    retrieval_summary: RetrievalSummaryResponse | None = None


class CreateRetrievalRequest(BaseModel):
    max_k: int = Field(default=10, ge=1, le=100, description="检索最大返回数量")


class RetrievalItemResponse(BaseModel):
    chunk_id: str
    score: float
    rank: int
    content: str = ""
    heading: str = ""
    source_file: str = ""
    is_ground_truth: bool = False


class RetrievalResponse(BaseModel):
    id: str
    golden_id: str
    max_k: int
    latency_ms: int
    embed_model_name: str = ""
    created_at: str = ""
    items: list[RetrievalItemResponse] = Field(default_factory=list)


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
