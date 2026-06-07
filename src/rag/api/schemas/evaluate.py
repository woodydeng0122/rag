from pydantic import BaseModel, Field


class EvaluateByProjectRequest(BaseModel):
    golden_ids: list[str] = Field(..., description="黄金记录 ID 列表")
    k_list: list[int] = Field(default=[10], description="Recall@K 的 K 值列表")


class EvaluateResponse(BaseModel):
    """评测结果 HTTP 响应体"""
    answerable_count: int
    recall: dict
    mrr: float
    failure: list[str]
    time: str = ""
    latency_total_ms: float = 0.0
    latency_avg_ms: float = 0.0
