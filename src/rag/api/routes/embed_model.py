from fastapi import APIRouter, Depends, HTTPException

from rag.api.schemas.embed_model import (
    EmbedModelItem, EmbedModelListResponse,
    CreateEmbedModelRequest, UpdateEmbedModelRequest,
)
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
    models = await container.embed_model_usecase.list()
    return EmbedModelListResponse(models=[_model_to_item(m) for m in models])


@router.get("/{model_id}", response_model=EmbedModelItem)
async def get_embed_model(
    model_id: str,
    container: Container = Depends(get_container),
):
    model = await container.embed_model_usecase.get(model_id)
    if model is None:
        raise HTTPException(status_code=404, detail="模型不存在")
    return _model_to_item(model)


@router.post("", response_model=EmbedModelItem)
async def create_embed_model(
    req: CreateEmbedModelRequest,
    container: Container = Depends(get_container),
):
    try:
        saved = await container.embed_model_usecase.create(
            name=req.name,
            dimension=req.dimension,
            description=req.description,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _model_to_item(saved)


@router.put("/{model_id}", response_model=EmbedModelItem)
async def update_embed_model(
    model_id: str,
    req: UpdateEmbedModelRequest,
    container: Container = Depends(get_container),
):
    try:
        updated = await container.embed_model_usecase.update(
            model_id=model_id,
            name=req.name,
            dimension=req.dimension,
            description=req.description,
        )
    except ValueError as e:
        if "不存在" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    return _model_to_item(updated)


@router.delete("/{model_id}")
async def delete_embed_model(
    model_id: str,
    container: Container = Depends(get_container),
):
    try:
        deleted = await container.embed_model_usecase.delete(model_id)
    except ValueError as e:
        if "不存在" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    if not deleted:
        raise HTTPException(status_code=500, detail="删除失败")
    return {"detail": "删除成功"}


@router.post("/status", response_model=EmbedModelListResponse)
async def refresh_embed_model_status(
    container: Container = Depends(get_container),
):
    """刷新所有嵌入模型的在线状态"""
    models = await container.scan_embed_models_usecase.execute()
    return EmbedModelListResponse(models=[_model_to_item(m) for m in models])
