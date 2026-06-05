from fastapi import APIRouter, Depends

from rag.api.schemas.ask import AskRequest, AskResponse
from rag.bootstrap.container import Container, get_container

router = APIRouter(prefix="/api/projects/{project_id}", tags=["问答"])


@router.post("/ask", response_model=AskResponse)
async def ask(
    project_id: str,
    req: AskRequest,
    container: Container = Depends(get_container),
) -> AskResponse:
    """根据查询检索相关分块并生成回答（需要 LLM API Key）"""
    return container.ask.execute(query=req.query, top_k=req.top_k)
