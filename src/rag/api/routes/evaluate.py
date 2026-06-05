from fastapi import APIRouter, Depends, HTTPException

from rag.api.schemas.evaluate import EvaluateByProjectRequest
from rag.application.results.evaluate_result import EvaluateResult
from rag.bootstrap.container import Container, get_container

router = APIRouter(prefix="/api/projects/{project_id}", tags=["评测"])


@router.post("/evaluations", response_model=EvaluateResult)
async def create_evaluation(
    project_id: str,
    req: EvaluateByProjectRequest,
    container: Container = Depends(get_container),
) -> EvaluateResult:
    """按项目执行评测，持久化结果"""
    try:
        return await container.evaluate.execute_by_project(
            project_id=project_id,
            golden_ids=req.golden_ids,
            k_list=req.k_list,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
