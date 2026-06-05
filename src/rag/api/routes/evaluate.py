from fastapi import APIRouter, Depends, HTTPException

from rag.api.schemas.evaluate import EvaluateByProjectRequest
from rag.application.results.evaluate_result import EvaluateResult
from rag.bootstrap.container import Container, get_container

router = APIRouter(prefix="/evaluate", tags=["评测"])


@router.post("/projects/{project_id}", response_model=EvaluateResult)
async def evaluate_by_project(
    project_id: str,
    req: EvaluateByProjectRequest,
    container: Container = Depends(get_container),
) -> EvaluateResult:
    """按项目和黄金记录 ID 列表执行评测，持久化结果"""
    try:
        return await container.evaluate.execute_by_project(
            project_id=project_id,
            golden_ids=req.golden_ids,
            k_list=req.k_list,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
