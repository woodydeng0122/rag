from pydantic import BaseModel, Field


class EvaluateRequest(BaseModel):
    records: list[dict] = Field(..., description="黄金测试记录列表")
    k_list: list[int] = Field(default=[10], description="Recall@K 的 K 值列表")


class EvaluateResponse(BaseModel):
    time: str = Field("", description="评测时间")
    embedding_file: str = Field("", description="向量文件")
    golden_file: str = Field("", description="黄金文件")
    embedder_model: str = Field("", description="嵌入模型")
    answerable_count: int = Field(0, description="可回答问题数量")
    recall: dict = Field(default_factory=dict, description="召回统计")
    mrr: float = Field(0.0, description="MRR")
    latency_total_ms: float = Field(0.0, description="总延迟（ms）")
    latency_avg_ms: float = Field(0.0, description="平均延迟（ms）")
    failure: list[str] = Field(default_factory=list, description="未命中的查询列表")
