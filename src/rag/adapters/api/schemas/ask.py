from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    query: str = Field(..., description="用户提问")
    top_k: int = Field(default=3, ge=1, le=100, description="参考分块数量")


class AskResponse(BaseModel):
    answer: str
    chunks: list[dict]
