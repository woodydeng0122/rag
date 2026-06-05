from fastapi import APIRouter, Depends, HTTPException

from rag.api.schemas.project import CreateProjectRequest, UpdateProjectRequest, ProjectResponse
from rag.domain.entities.project import Project
from rag.domain.ports.project_repository import ProjectRepositoryPort
from rag.bootstrap.container import Container, get_container

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _project_to_response(p: Project) -> ProjectResponse:
    return ProjectResponse(
        id=p.id,
        name=p.name,
        description=p.description,
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
    project = Project(name=req.name, description=req.description)
    saved = await container.project_repo.save(project)
    return _project_to_response(saved)


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    container: Container = Depends(get_container),
):
    projects = await container.project_repo.list()
    return [_project_to_response(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    container: Container = Depends(get_container),
):
    project = await container.project_repo.get_by_id(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    return _project_to_response(project)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    req: UpdateProjectRequest,
    container: Container = Depends(get_container),
):
    existing = await container.project_repo.get_by_id(project_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="项目不存在")

    existing.name = req.name
    existing.description = req.description
    updated = await container.project_repo.update(existing)
    return _project_to_response(updated)


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    container: Container = Depends(get_container),
):
    existing = await container.project_repo.get_by_id(project_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="项目不存在")

    deleted = await container.project_repo.delete(project_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="删除失败")
    return {"detail": "删除成功"}
