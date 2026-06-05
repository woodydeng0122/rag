from fastapi import APIRouter, Request, Depends

from rag.api.schemas.evaluate import EvaluateRequest, EvaluateResponse
from rag.application.usecases.evaluate import EvaluateUseCase


router = APIRouter(prefix="/evaluate", tags=["评测"])


def get_evaluate_usecase(request: Request) -> EvaluateUseCase:
    return request.app.state.container.evaluate


@router.post("/", response_model=EvaluateResponse)
def evaluate(
    req: EvaluateRequest,
    usecase: EvaluateUseCase = Depends(get_evaluate_usecase),
) -> EvaluateResponse:
    """对黄金测试集进行评测，返回 Recall@K、MRR、延迟等完整报告"""
    return usecase.execute(records=req.records, k_list=req.k_list)
