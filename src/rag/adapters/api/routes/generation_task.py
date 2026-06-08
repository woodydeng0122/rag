import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from rag.adapters.api.presenters.golden_dataset import GoldenDatasetPresenter
from rag.domain.entities.generation_task import TaskStatus
from rag.bootstrap.container import Container, get_container

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects/{project_id}", tags=["generation-tasks"])


@router.get("/generation-tasks")
async def list_generation_tasks(
    project_id: str,
    container: Container = Depends(get_container),
):
    tasks = await container.generation_task_usecase.list_tasks(project_id)
    return [GoldenDatasetPresenter.to_task_response(t) for t in tasks]


@router.get("/generation-tasks/{task_id}")
async def get_generation_task(
    project_id: str,
    task_id: str,
    container: Container = Depends(get_container),
):
    task = await container.generation_task_usecase.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="生成任务不存在")
    return GoldenDatasetPresenter.to_task_response(task)


@router.get("/generation-tasks/{task_id}/stream")
async def stream_generation_task(
    project_id: str,
    task_id: str,
    container: Container = Depends(get_container),
):
    """SSE 端点：实时推送生成过程事件"""
    task = await container.generation_task_usecase.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="生成任务不存在")

    # 如果任务已结束，推送最终状态后关闭
    if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
        async def _final_stream():
            if task.status == TaskStatus.COMPLETED:
                yield f"event: task_done\ndata: {json.dumps({'completed': task.completed, 'failed': task.failed})}\n\n"
            elif task.status == TaskStatus.FAILED:
                yield f"event: task_failed\ndata: {json.dumps({'error': task.error_message})}\n\n"
            elif task.status == TaskStatus.CANCELLED:
                yield "event: task_cancelled\ndata: {}\n\n"
        return StreamingResponse(_final_stream(), media_type="text/event-stream", headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        })

    # 查找活跃 Runner
    runner = container.task_manager.get(task_id)
    if runner is None:
        # Runner 不存在（可能服务重启），推送当前进度
        async def _progress_only():
            yield f"event: progress\ndata: {json.dumps({'completed': task.completed, 'total': task.total, 'failed': task.failed})}\n\n"
        return StreamingResponse(_progress_only(), media_type="text/event-stream", headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        })

    async def _event_stream():
        try:
            while True:
                event = await runner.event_queue.get()
                if event is None:
                    break  # 哨兵，Runner 已结束
                event_type = event.get("type", "progress")
                sse_event_map = {
                    "progress": "progress",
                    "phase_start": "phase_start",
                    "llm_token": "llm_token",
                    "llm_done": "llm_done",
                    "question_generated": "question_generated",
                    "result": "result",
                    "task_done": "task_done",
                    "task_failed": "task_failed",
                    "task_cancelled": "task_cancelled",
                    "task_paused": "task_paused",
                    "task_resumed": "task_resumed",
                }
                event_name = sse_event_map.get(event_type, event_type)
                data = {k: v for k, v in event.items() if k != "type"}
                yield f"event: {event_name}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.exception("SSE 流异常")
            yield f"event: task_failed\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(_event_stream(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


@router.post("/generation-tasks/{task_id}/pause")
async def pause_generation_task(
    project_id: str,
    task_id: str,
    container: Container = Depends(get_container),
):
    """暂停生成任务"""
    try:
        await container.generation_task_usecase.pause_task(task_id, container.task_manager)
    except ValueError as e:
        if "不存在" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    return {"detail": "任务已暂停"}


@router.post("/generation-tasks/{task_id}/resume")
async def resume_generation_task(
    project_id: str,
    task_id: str,
    container: Container = Depends(get_container),
):
    """继续生成任务"""
    try:
        await container.generation_task_usecase.resume_task(task_id, container.task_manager)
    except ValueError as e:
        if "不存在" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    return {"detail": "任务已继续"}


@router.delete("/generation-tasks/{task_id}")
async def cancel_generation_task(
    project_id: str,
    task_id: str,
    container: Container = Depends(get_container),
):
    """取消生成任务"""
    try:
        await container.generation_task_usecase.cancel_task(task_id, container.task_manager)
    except ValueError as e:
        if "不存在" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    return {"detail": "任务已取消"}


@router.post("/generation-tasks/{task_id}/retry-failed")
async def retry_failed_generation(
    project_id: str,
    task_id: str,
    container: Container = Depends(get_container),
):
    """重试失败项"""
    try:
        retry_count = await container.generation_task_usecase.retry_failed_task(
            task_id, container.task_manager
        )
    except ValueError as e:
        if "不存在" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    return {"detail": f"正在重试 {retry_count} 个失败项"}
