from fastapi import APIRouter, Depends, HTTPException

from rag.adapters.api.dependencies import get_current_user
from rag.adapters.api.presenters.project import ProjectPresenter
from rag.adapters.api.schemas.project import (
    CreateProjectRequest,
    EvaluationStatsRequest,
    EvaluationStatsResponse,
    UpdateEvaluationRemarkRequest,
    UpdateProjectRequest,
)
from rag.bootstrap.container import Container, get_container
from rag.domain.entities.user import User

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("")
async def create_project(
    req: CreateProjectRequest,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
):
    try:
        saved = await container.project_usecase.create(
            name=req.name,
            description=req.description,
            embed_model_id=req.embed_model_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    result = await container.project_usecase.get_with_model_name(saved.id)
    return ProjectPresenter.to_response(result)


@router.get("")
async def list_projects(
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
):
    results = await container.project_usecase.list_with_model_name(current_user.id)
    return [ProjectPresenter.to_response(r) for r in results]


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
):
    try:
        deleted = await container.project_usecase.delete(project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    if not deleted:
        raise HTTPException(status_code=500, detail="删除失败")
    return {"detail": "删除成功"}


@router.post("/{project_id}/evaluation-stats", response_model=EvaluationStatsResponse)
async def create_evaluation_stats(
    project_id: str,
    req: EvaluationStatsRequest,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
):
    """触发项目评估统计 — 基于已有检索结果计算 recall@{top_k}、MRR 等指标"""
    try:
        result = await container.evaluation_usecase.execute(
            project_id=project_id, top_k=req.top_k, remark=req.remark
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _evaluation_to_response(result)


@router.get("/{project_id}/evaluation-stats", response_model=list[EvaluationStatsResponse])
async def list_evaluation_stats(
    project_id: str,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
):
    """查询项目评估历史"""
    results = await container.evaluation_usecase.list_evaluations(project_id)
    return [_evaluation_to_response(r) for r in results]


@router.delete("/{project_id}/evaluation-stats/{evaluation_id}")
async def delete_evaluation_stats(
    project_id: str,
    evaluation_id: str,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
):
    """删除评估记录"""
    try:
        await container.evaluation_usecase.delete_evaluation(evaluation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"detail": "删除成功"}


@router.patch("/{project_id}/evaluation-stats/{evaluation_id}", response_model=EvaluationStatsResponse)
async def update_evaluation_remark(
    project_id: str,
    evaluation_id: str,
    req: UpdateEvaluationRemarkRequest,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
):
    """更新评估记录备注"""
    try:
        await container.evaluation_usecase.update_remark(evaluation_id, req.remark)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    results = await container.evaluation_usecase.list_evaluations(project_id)
    target = next((r for r in results if r.id == evaluation_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="评估记录不存在")
    return _evaluation_to_response(target)


def _evaluation_to_response(evaluation) -> EvaluationStatsResponse:
    return EvaluationStatsResponse(
        id=evaluation.id,
        project_id=evaluation.project_id,
        top_k=evaluation.top_k,
        golden_total=evaluation.golden_total,
        golden_retrieved=evaluation.golden_retrieved,
        recall_at_k=evaluation.recall_at_k,
        mrr=evaluation.mrr,
        hit_rate=evaluation.hit_rate,
        full_hit_count=evaluation.full_hit_count,
        zero_hit_count=evaluation.zero_hit_count,
        avg_latency_ms=evaluation.avg_latency_ms,
        avg_embed_latency_ms=evaluation.avg_embed_latency_ms,
        avg_search_latency_ms=evaluation.avg_search_latency_ms,
        strategy=evaluation.strategy.value,
        embed_model_name=evaluation.embed_model_name,
        remark=evaluation.remark,
        created_at=evaluation.created_at.isoformat() if evaluation.created_at else "",
    )
