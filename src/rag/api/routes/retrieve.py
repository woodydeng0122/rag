from fastapi import APIRouter, Depends

from rag.api.schemas.retrieve import RetrieveRequest, RetrieveResponse
from rag.bootstrap.container import Container, get_container

router = APIRouter(prefix="/api/projects/{project_id}", tags=["检索"])


@router.post("/retrievals", response_model=RetrieveResponse)
async def create_retrieval(
    project_id: str,
    req: RetrieveRequest,
    container: Container = Depends(get_container),
) -> RetrieveResponse:
    """根据查询检索相关文档分块"""
    return container.retrieve.execute(query=req.query, top_k=req.top_k)
