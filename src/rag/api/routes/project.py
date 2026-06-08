from fastapi import APIRouter, Depends, HTTPException

from rag.api.presenters.project import ProjectPresenter
from rag.api.schemas.project import CreateProjectRequest, UpdateProjectRequest
from rag.bootstrap.container import Container, get_container

router = APIRouter(prefix="/api/projects", tags=["projects"])


async def _project_to_response(p, container: Container):
    embed_model_name = ""
    if p.embed_model_id:
        embed_model = await container.embed_model_usecase.get(p.embed_model_id)
        if embed_model:
            embed_model_name = embed_model.name

    return ProjectPresenter.to_response(p, embed_model_name=embed_model_name)


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
    return await _project_to_response(saved, container)


@router.get("")
async def list_projects(
    container: Container = Depends(get_container),
):
    projects = await container.project_usecase.list()
    return [await _project_to_response(p, container) for p in projects]


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    container: Container = Depends(get_container),
):
    project = await container.project_usecase.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    return await _project_to_response(project, container)


@router.put("/{project_id}")
async def update_project(
    project_id: str,
    req: UpdateProjectRequest,
    container: Container = Depends(get_container),
):
    try:
        updated = await container.project_usecase.update(
            project_id=project_id,
            name=req.name,
            description=req.description,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return await _project_to_response(updated, container)


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
