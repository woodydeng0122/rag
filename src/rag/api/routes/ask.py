from fastapi import APIRouter, Request, Depends

from rag.api.schemas.ask import AskRequest, AskResponse
from rag.application.usecases.ask import AskUseCase


router = APIRouter(prefix="/ask", tags=["问答"])


def get_ask_usecase(request: Request) -> AskUseCase:
    return request.app.state.container.ask


@router.post("/", response_model=AskResponse)
def ask(
    req: AskRequest,
    usecase: AskUseCase = Depends(get_ask_usecase),
) -> AskResponse:
    """根据查询检索相关分块并生成回答（需要 LLM API Key）"""
    return usecase.execute(query=req.query, top_k=req.top_k)
