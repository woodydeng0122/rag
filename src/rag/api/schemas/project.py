from pydantic import BaseModel


class CreateProjectRequest(BaseModel):
    name: str
    description: str = ""
    embed_model_id: str


class UpdateProjectRequest(BaseModel):
    name: str
    description: str = ""


class EvalSummaryResponse(BaseModel):
    recall_at_10: float | None = None
    mrr: float | None = None
    answerable: int | None = None
    total: int | None = None
    latency_avg_ms: float | None = None
    evaluated_at: str | None = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str
    embed_model_id: str = ""
    embed_model_name: str = ""
    embed_dimension: int = 512
    created_at: str = ""
    updated_at: str = ""
    eval_summary: EvalSummaryResponse | None = None
