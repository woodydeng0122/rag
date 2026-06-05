from pydantic import BaseModel


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
    # 评测汇总字段
    eval_recall_at_10: float | None = None
    eval_mrr: float | None = None
    eval_answerable: int | None = None
    eval_total: int | None = None
    eval_latency_avg_ms: float | None = None
    evaluated_at: str | None = None


class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]
