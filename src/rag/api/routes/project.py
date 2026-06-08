from fastapi import APIRouter, Depends, HTTPException

from rag.api.presenters.project import ProjectPresenter
from rag.api.schemas.project import CreateProjectRequest, UpdateProjectRequest
from rag.bootstrap.container import Container, get_container

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("")
async def create_project(
    req: CreateProjectRequest,
    container: Container = Depends(get_container),
):
    try:
        saved = await container.project_usecase.create(
            name=req.name,
            description=req.description,
            embed_model_id=req.embed_model_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    result = await container.project_usecase.get_with_model_name(saved.id)
    return ProjectPresenter.to_response(result)


@router.get("")
async def list_projects(
    container: Container = Depends(get_container),
):
    results = await container.project_usecase.list_with_model_name()
    return [ProjectPresenter.to_response(r) for r in results]


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    container: Container = Depends(get_container),
):
    result = await container.project_usecase.get_with_model_name(project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    return ProjectPresenter.to_response(result)


@router.put("/{project_id}")
async def update_project(
    project_id: str,
    req: UpdateProjectRequest,
    container: Container = Depends(get_container),
):
    try:
        await container.project_usecase.update(
            project_id=project_id,
            name=req.name,
            description=req.description,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    result = await container.project_usecase.get_with_model_name(project_id)
    return ProjectPresenter.to_response(result)


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    container: Container = Depends(get_container),
):
    try:
        deleted = await container.project_usecase.delete(project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    if not deleted:
        raise HTTPException(status_code=500, detail="删除失败")
    return {"detail": "删除成功"}
