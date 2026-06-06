from pydantic import BaseModel

from rag.domain.entities.embed_model import ModelStatus


class EmbedModelItem(BaseModel):
    id: str
    name: str
    dimension: int
    description: str = ""
    status: ModelStatus = ModelStatus.OFFLINE
    config: dict = {}
    created_at: str = ""
    updated_at: str = ""


class EmbedModelListResponse(BaseModel):
    models: list[EmbedModelItem]


class CreateEmbedModelRequest(BaseModel):
    name: str
    description: str = ""
    dimension: int = 0  # 本地无 config.json 时由用户指定


class UpdateEmbedModelRequest(BaseModel):
    name: str
    description: str = ""
