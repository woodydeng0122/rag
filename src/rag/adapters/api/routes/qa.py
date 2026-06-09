import json
import logging
import traceback

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from rag.adapters.api.schemas.qa import (
    CreateSessionRequest,
    SessionResponse,
    MessageResponse,
    AskStreamRequest,
)
from rag.bootstrap.container import Container, get_container

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects/{project_id}", tags=["问答"])


@router.post("/qa/sessions", response_model=SessionResponse)
async def create_session(
    project_id: str,
    req: CreateSessionRequest = CreateSessionRequest(),
    container: Container = Depends(get_container),
):
    """创建问答会话"""
    return await container.qa.create_session(project_id, req.title)


@router.get("/qa/sessions", response_model=list[SessionResponse])
async def list_sessions(
    project_id: str,
    container: Container = Depends(get_container),
):
    """获取项目的所有问答会话"""
    return await container.qa.list_sessions(project_id)


@router.get("/qa/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    project_id: str,
    session_id: str,
    container: Container = Depends(get_container),
):
    """获取会话详情"""
    result = await container.qa.get_session(session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return result


@router.delete("/qa/sessions/{session_id}")
async def delete_session(
    project_id: str,
    session_id: str,
    container: Container = Depends(get_container),
):
    """删除会话及其所有消息"""
    deleted = await container.qa.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"detail": "删除成功"}


@router.get("/qa/sessions/{session_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    project_id: str,
    session_id: str,
    container: Container = Depends(get_container),
):
    """获取会话的所有消息"""
    return await container.qa.get_messages(session_id)


@router.post("/qa/sessions/{session_id}/ask")
async def ask_stream(
    project_id: str,
    session_id: str,
    req: AskStreamRequest,
    container: Container = Depends(get_container),
):
    """流式问答 — SSE 逐 token 返回"""

    # 校验会话存在
    session = await container.qa.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在")

    async def event_generator():
        try:
            async for event in container.qa.ask_stream(
                session_id=session_id,
                query=req.query,
                project_id=project_id,
                top_k=req.top_k,
            ):
                if event.type == "sources":
                    data = json.dumps(
                        {
                            "type": "sources",
                            "chunks": [
                                {
                                    "chunk_id": c.chunk_id,
                                    "content": c.content,
                                    "score": c.score,
                                    "source_file": c.source_file,
                                    "heading": c.heading,
                                }
                                for c in event.chunks
                            ],
                        },
                        ensure_ascii=False,
                    )
                    yield f"data: {data}\n\n"
                elif event.type == "chunk":
                    data = json.dumps({"type": "chunk", "data": event.data}, ensure_ascii=False)
                    yield f"data: {data}\n\n"
                elif event.type == "done":
                    data = json.dumps({"type": "done", "latency_ms": event.latency_ms}, ensure_ascii=False)
                    yield f"data: {data}\n\n"
                elif event.type == "error":
                    data = json.dumps({"type": "error", "data": event.data}, ensure_ascii=False)
                    yield f"data: {data}\n\n"
        except Exception as e:
            logger.error(f"SSE 流式问答异常 session_id={session_id} query={req.query}\n{traceback.format_exc()}")
            data = json.dumps({"type": "error", "data": str(e)}, ensure_ascii=False)
            yield f"data: {data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
