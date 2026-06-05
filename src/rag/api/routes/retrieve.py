from fastapi import APIRouter, Request, Depends

from rag.api.schemas.retrieve import RetrieveRequest, RetrieveResponse, RetrieveResult, ChunkResponse
from rag.application.usecases.retrieve import RetrieveUseCase


router = APIRouter(prefix="/retrieve", tags=["检索"])


def get_retrieve_usecase(request: Request) -> RetrieveUseCase:
    return request.app.state.container.retrieve


@router.post("/", response_model=RetrieveResponse)
def retrieve(
    req: RetrieveRequest,
    usecase: RetrieveUseCase = Depends(get_retrieve_usecase),
) -> RetrieveResponse:
    """根据查询检索相关文档分块"""
    return usecase.execute(query=req.query, top_k=req.top_k)
