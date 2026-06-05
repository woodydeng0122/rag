from pydantic import BaseModel, Field


class CreateGoldenDatasetRequest(BaseModel):
    query: str = Field(..., description="查询文本")
    ground_truth_chunks: list[str] = Field(..., description="关联的真实分块 ID 列表")
    reference_answer: str = Field("", description="参考答案")


class UpdateGoldenDatasetRequest(BaseModel):
    query: str = Field(..., description="查询文本")
    ground_truth_chunks: list[str] = Field(..., description="关联的真实分块 ID 列表")
    reference_answer: str = Field("", description="参考答案")


class GoldenDatasetResponse(BaseModel):
    id: str
    project_id: str
    query: str
    ground_truth_chunks: list[str]
    reference_answer: str = ""
    retrieved_chunk_ids: list[str] = Field(default_factory=list)
    is_hit: bool | None = None
    hit_rank: int | None = None
    evaluated_at: str | None = None
    created_at: str = ""
    metadata: dict = Field(default_factory=dict)


class SkippedRecordResponse(BaseModel):
    row: int
    reason: str


class ImportGoldenDatasetResponse(BaseModel):
    success_count: int = 0
    skipped_count: int = 0
    skipped: list[SkippedRecordResponse] = Field(default_factory=list)
