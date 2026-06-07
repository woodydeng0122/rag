from pydantic import BaseModel, Field


class RetrieveRequest(BaseModel):
    query: str = Field(..., description="检索查询")
    top_k: int = Field(default=3, ge=1, le=100, description="返回数量")


class ChunkResponse(BaseModel):
    chunk_id: str
    content: str
    source_file: str = ""
    heading: str = ""


class RetrievedChunkResponse(BaseModel):
    chunk_id: str
    score: float
    chunk: ChunkResponse | None = None


class RetrieveResponse(BaseModel):
    results: list[RetrievedChunkResponse]
