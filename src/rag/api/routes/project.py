from fastapi import APIRouter, Depends, HTTPException

from rag.api.schemas.project import CreateProjectRequest, UpdateProjectRequest, ProjectResponse
from rag.domain.entities.project import Project
from rag.domain.entities.embed_model import EmbedModel
from rag.bootstrap.container import Container, get_container

router = APIRouter(prefix="/api/projects", tags=["projects"])


async def _project_to_response(p: Project, container: Container) -> ProjectResponse:
    embed_model_name = ""
    if p.embed_model_id:
        embed_model = await container.embed_model_usecase.get(p.embed_model_id)
        if embed_model:
            embed_model_name = embed_model.name

    return ProjectResponse(
        id=p.id,
        name=p.name,
        description=p.description,
        embed_model_id=p.embed_model_id,
        embed_model_name=embed_model_name,
        embed_dimension=p.embed_dimension,
        created_at=p.created_at.isoformat() if p.created_at else "",
        updated_at=p.updated_at.isoformat() if p.updated_at else "",
        eval_recall_at_10=p.eval_recall_at_10,
        eval_mrr=p.eval_mrr,
        eval_answerable=p.eval_answerable,
        eval_total=p.eval_total,
        eval_latency_avg_ms=p.eval_latency_avg_ms,
        evaluated_at=p.evaluated_at.isoformat() if p.evaluated_at else None,
    )


@router.post("", response_model=ProjectResponse)
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


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    container: Container = Depends(get_container),
):
    projects = await container.project_usecase.list()
    return [await _project_to_response(p, container) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    container: Container = Depends(get_container),
):
    project = await container.project_usecase.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    return await _project_to_response(project, container)


@router.put("/{project_id}", response_model=ProjectResponse)
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
