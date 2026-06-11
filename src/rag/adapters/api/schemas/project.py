from pydantic import BaseModel, Field


class CreateProjectRequest(BaseModel):
    name: str
    description: str = ""
    embed_model_id: str


class UpdateProjectRequest(BaseModel):
    name: str
    description: str = ""


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str
    embed_model_id: str = ""
    embed_model_name: str = ""
    embed_dimension: int = 512
    created_at: str = ""
    updated_at: str = ""


class EvaluationStatsRequest(BaseModel):
    top_k: int = Field(default=10, ge=1, le=100, description="截断排名，计算 recall@{top_k}")
    remark: str = Field(default="", max_length=500, description="备注")


class EvaluationStatsResponse(BaseModel):
    id: str
    project_id: str
    top_k: int
    golden_total: int
    golden_retrieved: int
    recall_at_k: float
    mrr: float
    hit_rate: float
    full_hit_count: int
    zero_hit_count: int
    avg_latency_ms: float
    avg_embed_latency_ms: float
    avg_search_latency_ms: float
    embed_model_name: str = ""
    remark: str = ""
    created_at: str = ""


class UpdateEvaluationRemarkRequest(BaseModel):
    remark: str = Field(default="", max_length=500, description="备注")
