from rag.api.schemas.embed_model import EmbedModelItem, EmbedModelStatus
from rag.domain.entities.embed_model import EmbedModel


class EmbedModelPresenter:
    """嵌入模型领域实体 → API 响应转换"""

    @staticmethod
    def to_item(m: EmbedModel) -> EmbedModelItem:
        return EmbedModelItem(
            id=m.id,
            name=m.name,
            dimension=m.dimension,
            description=m.description,
            status=EmbedModelStatus(m.status.value),
            config=m.config.to_dict(),
            created_at=m.created_at.isoformat() if m.created_at else "",
            updated_at=m.updated_at.isoformat() if m.updated_at else "",
        )
