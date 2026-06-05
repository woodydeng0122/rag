from pydantic import BaseModel


class EmbedModelItem(BaseModel):
    id: str
    name: str
    dimension: int
    description: str = ""
    status: str = "offline"
    created_at: str = ""
    updated_at: str = ""


class EmbedModelListResponse(BaseModel):
    models: list[EmbedModelItem]
