from rag.adapters.api.schemas.embed_model import EmbedModelItem, EmbedModelStatus
from rag.domain.entities.embed_model import EmbedModel, ModelStatus

# 领域枚举 → API 枚举映射
_DOMAIN_TO_API_MODEL_STATUS = {
    ModelStatus.ONLINE: EmbedModelStatus.ONLINE,
    ModelStatus.OFFLINE: EmbedModelStatus.OFFLINE,
}


class EmbedModelPresenter:
    """嵌入模型领域实体 → API 响应转换"""

    @staticmethod
    def to_item(m: EmbedModel) -> EmbedModelItem:
        return EmbedModelItem(
            id=m.id,
            name=m.name,
            model_type=m.model_type,
            dimension=m.dimension,
            description=m.description,
            status=_DOMAIN_TO_API_MODEL_STATUS[m.status],
            config=m.config.to_dict(),
            created_at=m.created_at.isoformat() if m.created_at else "",
            updated_at=m.updated_at.isoformat() if m.updated_at else "",
        )
