from enum import Enum

from pydantic import BaseModel


class EmbedModelStatus(str, Enum):
    """API 层模型状态枚举 — 与领域层解耦"""
    ONLINE = "online"
    OFFLINE = "offline"


class EmbedModelItem(BaseModel):
    id: str
    name: str
    dimension: int
    description: str = ""
    status: EmbedModelStatus = EmbedModelStatus.OFFLINE
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
