from pydantic import BaseModel, Field


class EvaluateByProjectRequest(BaseModel):
    golden_ids: list[str] = Field(..., description="黄金记录 ID 列表")
    k_list: list[int] = Field(default=[10], description="Recall@K 的 K 值列表")
