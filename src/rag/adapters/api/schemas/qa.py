from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    title: str = Field(default="", max_length=512, description="会话标题")


class SessionResponse(BaseModel):
    id: str
    project_id: str
    title: str
    created_at: str
    updated_at: str


class MessageChunkResponse(BaseModel):
    chunk_id: str
    content: str
    score: float
    source_file: str
    heading: str


class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    chunks: list[MessageChunkResponse] = []
    latency_ms: int | None = None
    created_at: str = ""


class AskStreamRequest(BaseModel):
    query: str = Field(..., description="用户提问")
    top_k: int = Field(default=3, ge=1, le=100, description="参考分块数量")
