from fastapi import APIRouter, Depends

from rag.api.schemas.embed_model import EmbedModelItem, EmbedModelListResponse
from rag.bootstrap.container import Container, get_container

router = APIRouter(prefix="/api/embed-models", tags=["embed-models"])


def _model_to_item(m) -> EmbedModelItem:
    return EmbedModelItem(
        id=m.id,
        name=m.name,
        dimension=m.dimension,
        description=m.description,
        status=m.status,
        created_at=m.created_at.isoformat() if m.created_at else "",
        updated_at=m.updated_at.isoformat() if m.updated_at else "",
    )


@router.get("", response_model=EmbedModelListResponse)
async def list_embed_models(
    container: Container = Depends(get_container),
):
    models = await container.embed_model_repo.get_all()
    return EmbedModelListResponse(models=[_model_to_item(m) for m in models])


@router.put("/status", response_model=EmbedModelListResponse)
async def refresh_embed_model_status(
    container: Container = Depends(get_container),
):
    """刷新所有嵌入模型的在线状态"""
    models = await container.scan_embed_models_usecase.execute()
    return EmbedModelListResponse(models=[_model_to_item(m) for m in models])
