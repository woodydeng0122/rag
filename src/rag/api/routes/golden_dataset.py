import asyncio
import csv
import io
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse

from rag.api.schemas.golden_dataset import (
    CreateGoldenDatasetRequest,
    UpdateGoldenDatasetRequest,
    GoldenDatasetResponse,
    EvaluationMetricsResponse,
    ImportGoldenDatasetResponse,
    SkippedRecordResponse,
    GenerateGoldenRequest,
    GenerateGoldenResponse,
    GenerationTaskResponse,
    BatchStatusUpdateRequest,
    BatchStatusUpdateResponse,
)
from rag.application.usecases.generation_task_runner import GenerationTaskRunner
from rag.domain.entities.chunk import Chunk
from rag.domain.entities.generation_task import TaskStatus
from rag.domain.value_objects.generate_config import GenerateConfig
from rag.bootstrap.container import Container, get_container

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects/{project_id}", tags=["golden-datasets"])

MAX_IMPORT_ROWS = 1000


def _record_to_response(r) -> GoldenDatasetResponse:
    evaluation = None
    if r.evaluation:
        evaluation = EvaluationMetricsResponse(
            retrieved_chunk_ids=r.evaluation.retrieved_chunk_ids or [],
            is_hit=r.evaluation.is_hit,
            hit_rank=r.evaluation.hit_rank,
            evaluated_at=r.evaluation.evaluated_at.isoformat() if r.evaluation.evaluated_at else None,
        )
    return GoldenDatasetResponse(
        id=r.id,
        project_id=r.project_id,
        query=r.query,
        ground_truth_chunks=r.ground_truth_chunks,
        reference_answer=r.reference_answer or "",
        status=r.status.value if hasattr(r.status, "value") else r.status,
        evaluation=evaluation,
        created_at=r.created_at.isoformat() if r.created_at else "",
        metadata=r.metadata if r.metadata else {},
    )


def _task_to_response(t) -> GenerationTaskResponse:
    return GenerationTaskResponse(
        id=t.id,
        project_id=t.project_id,
        status=t.status.value if hasattr(t.status, "value") else t.status,
        total=t.total,
        completed=t.completed,
        failed=t.failed,
        document_ids=t.document_ids or [],
        chunk_ids=t.chunk_ids or [],
        config=t.config.to_dict() if t.config else {},
        error_message=t.error_message or "",
        created_at=t.created_at.isoformat() if t.created_at else "",
        updated_at=t.updated_at.isoformat() if t.updated_at else None,
        finished_at=t.finished_at.isoformat() if t.finished_at else None,
    )


@router.get("/golden-datasets", response_model=list[GoldenDatasetResponse])
async def list_golden_datasets(
    project_id: str,
    status: str | None = None,
    container: Container = Depends(get_container),
):
    records = await container.golden_dataset_usecase.list_by_project(project_id, status=status)
    return [_record_to_response(r) for r in records]


@router.get("/documents/{document_id}/golden-datasets", response_model=list[GoldenDatasetResponse])
async def list_golden_datasets_by_document(
    project_id: str,
    document_id: str,
    container: Container = Depends(get_container),
):
    """按文档 ID 查询关联的黄金记录"""
    records = await container.golden_dataset_usecase.list_by_document(project_id, document_id)
    return [_record_to_response(r) for r in records]


@router.post("/golden-datasets", response_model=GoldenDatasetResponse)
async def create_golden_dataset(
    project_id: str,
    req: CreateGoldenDatasetRequest,
    container: Container = Depends(get_container),
):
    record = await container.golden_dataset_usecase.create(
        project_id=project_id,
        query=req.query,
        ground_truth_chunks=req.ground_truth_chunks,
        reference_answer=req.reference_answer,
    )
    return _record_to_response(record)


@router.patch("/golden-datasets/{record_id}", response_model=GoldenDatasetResponse)
async def update_golden_dataset(
    project_id: str,
    record_id: str,
    req: UpdateGoldenDatasetRequest,
    container: Container = Depends(get_container),
):
    try:
        # 先获取当前记录，用请求中的非 None 字段覆盖
        current = await container.golden_dataset_usecase.get(record_id)
        if current is None:
            raise ValueError(f"黄金记录 {record_id} 不存在")
        record = await container.golden_dataset_usecase.update(
            record_id=record_id,
            query=req.query if req.query is not None else current.query,
            ground_truth_chunks=req.ground_truth_chunks if req.ground_truth_chunks is not None else current.ground_truth_chunks,
            reference_answer=req.reference_answer if req.reference_answer is not None else current.reference_answer,
            status=req.status,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _record_to_response(record)


@router.delete("/golden-datasets/{record_id}")
async def delete_golden_dataset(
    project_id: str,
    record_id: str,
    container: Container = Depends(get_container),
):
    deleted = await container.golden_dataset_usecase.delete(record_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="黄金记录不存在")
    return {"detail": "删除成功"}


@router.post("/golden-datasets/generate", response_model=GenerateGoldenResponse)
async def generate_golden_dataset(
    project_id: str,
    req: GenerateGoldenRequest,
    container: Container = Depends(get_container),
):
    """提交 LLM 生成黄金数据集任务"""
    if not req.document_ids and not req.chunk_ids:
        raise HTTPException(status_code=400, detail="必须提供 document_ids 或 chunk_ids")

    config = GenerateConfig()
    if req.config:
        config = GenerateConfig(
            per_chunk=req.config.per_chunk,
            question_types=req.config.resolve_question_types() or config.question_types,
            difficulty=req.config.difficulty,
            user_persona=req.config.user_persona,
            chunk_batch_size=req.config.chunk_batch_size,
            file_char_threshold=req.config.file_char_threshold,
        )

    # 加载目标 chunks
    chunk_repo = container.generate_golden_usecase.chunk_repo
    chunks_by_doc: dict[str, list[Chunk]] = {}
    try:
        if req.chunk_ids:
            all_chunks = await chunk_repo.list_by_project(project_id, limit=10000, offset=0)
            selected = {c for c in all_chunks if c.id in set(req.chunk_ids)}
            for c in selected:
                chunks_by_doc.setdefault(c.source_file, []).append(c)
        elif req.document_ids:
            for doc_id in req.document_ids:
                doc_chunks = await chunk_repo.list_by_document(doc_id)
                chunks_by_doc[doc_id] = doc_chunks
        else:
            raise ValueError("必须提供 document_ids 或 chunk_ids")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    total_chunks = sum(len(v) for v in chunks_by_doc.values())
    estimated_total = config.estimate_total(total_chunks)

    # 创建任务
    from rag.domain.entities.generation_task import GenerationTask
    task = GenerationTask(
        project_id=project_id,
        status=TaskStatus.RUNNING,
        total=estimated_total,
        document_ids=req.document_ids or [],
        chunk_ids=req.chunk_ids or [],
        config=config,
    )
    task_repo = container.generate_golden_usecase.task_repo
    task = await task_repo.save(task)

    # 创建 Runner 并注册到 TaskManager
    runner = GenerationTaskRunner(
        llm=container.generate_golden_usecase.llm,
        golden_repo=container.generate_golden_usecase.golden_repo,
        chunk_repo=chunk_repo,
        task_repo=task_repo,
    )
    container.task_manager.register(task.id, runner)

    # 启动后台协程
    async def _run_and_cleanup():
        try:
            async for _ in runner.run(task, project_id, chunks_by_doc, config):
                pass
        finally:
            container.task_manager.remove(task.id)

    asyncio.create_task(_run_and_cleanup())

    return GenerateGoldenResponse(task_id=task.id, status=task.status.value)


@router.get("/generation-tasks", response_model=list[GenerationTaskResponse])
async def list_generation_tasks(
    project_id: str,
    container: Container = Depends(get_container),
):
    tasks = await container.generate_golden_usecase.list_tasks(project_id)
    return [_task_to_response(t) for t in tasks]


@router.get("/generation-tasks/{task_id}", response_model=GenerationTaskResponse)
async def get_generation_task(
    project_id: str,
    task_id: str,
    container: Container = Depends(get_container),
):
    task = await container.generate_golden_usecase.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="生成任务不存在")
    return _task_to_response(task)


# ========== SSE 事件流 ==========


@router.get("/generation-tasks/{task_id}/stream")
async def stream_generation_task(
    project_id: str,
    task_id: str,
    container: Container = Depends(get_container),
):
    """SSE 端点：实时推送生成过程事件"""
    task = await container.generate_golden_usecase.get_task(task_id)
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
        return StreamingResponse(_final_stream(), media_type="text/event-stream")

    # 查找活跃 Runner
    runner = container.task_manager.get(task_id)
    if runner is None:
        # Runner 不存在（可能服务重启），推送当前进度
        async def _progress_only():
            yield f"event: progress\ndata: {json.dumps({'completed': task.completed, 'total': task.total, 'failed': task.failed})}\n\n"
        return StreamingResponse(_progress_only(), media_type="text/event-stream")

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

    return StreamingResponse(_event_stream(), media_type="text/event-stream")


# ========== 任务控制端点 ==========


@router.post("/generation-tasks/{task_id}/pause")
async def pause_generation_task(
    project_id: str,
    task_id: str,
    container: Container = Depends(get_container),
):
    """暂停生成任务"""
    task = await container.generate_golden_usecase.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="生成任务不存在")
    if task.status != TaskStatus.RUNNING:
        raise HTTPException(status_code=400, detail=f"无法暂停状态为 {task.status.value} 的任务")

    runner = container.task_manager.get(task_id)
    if runner:
        runner.pause_event.clear()

    task.pause()
    await container.generate_golden_usecase.task_repo.update(task)
    return {"detail": "任务已暂停"}


@router.post("/generation-tasks/{task_id}/resume")
async def resume_generation_task(
    project_id: str,
    task_id: str,
    container: Container = Depends(get_container),
):
    """继续生成任务"""
    task = await container.generate_golden_usecase.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="生成任务不存在")
    if task.status != TaskStatus.PAUSED:
        raise HTTPException(status_code=400, detail=f"无法继续状态为 {task.status.value} 的任务")

    runner = container.task_manager.get(task_id)
    if runner:
        runner.pause_event.set()

    task.resume()
    await container.generate_golden_usecase.task_repo.update(task)
    return {"detail": "任务已继续"}


@router.delete("/generation-tasks/{task_id}")
async def cancel_generation_task(
    project_id: str,
    task_id: str,
    container: Container = Depends(get_container),
):
    """取消生成任务"""
    task = await container.generate_golden_usecase.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="生成任务不存在")
    if task.status not in (TaskStatus.RUNNING, TaskStatus.PAUSED):
        raise HTTPException(status_code=400, detail=f"无法取消状态为 {task.status.value} 的任务")

    runner = container.task_manager.get(task_id)
    if runner:
        runner.cancel_flag.set()
        if task.status == TaskStatus.PAUSED:
            runner.pause_event.set()  # 解除暂停以便 Runner 能检查取消标志

    task.cancel()
    await container.generate_golden_usecase.task_repo.update(task)
    container.task_manager.remove(task_id)
    return {"detail": "任务已取消"}


@router.post("/generation-tasks/{task_id}/retry-failed")
async def retry_failed_generation(
    project_id: str,
    task_id: str,
    container: Container = Depends(get_container),
):
    """重试失败项"""
    task = await container.generate_golden_usecase.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="生成任务不存在")
    if task.status not in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
        raise HTTPException(status_code=400, detail="只能重试已完成或已取消的任务")

    runner = container.task_manager.get(task_id)
    if runner is None or not runner.failed_items:
        raise HTTPException(status_code=400, detail="没有失败项可重试")

    # 恢复任务状态为 running
    task.status = TaskStatus.RUNNING
    await container.generate_golden_usecase.task_repo.update(task)

    # 重新注册 Runner 并启动重试
    container.task_manager.register(task_id, runner)
    runner.pause_event.set()
    runner.cancel_flag.clear()

    async def _retry_and_cleanup():
        try:
            async for _ in runner.retry_failed():
                pass
        finally:
            container.task_manager.remove(task_id)

    asyncio.create_task(_retry_and_cleanup())

    return {"detail": f"正在重试 {len(runner.failed_items)} 个失败项"}


@router.post("/golden-datasets/batch-approve", response_model=BatchStatusUpdateResponse)
async def batch_approve(
    project_id: str,
    req: BatchStatusUpdateRequest,
    container: Container = Depends(get_container),
):
    count = await container.golden_dataset_usecase.batch_approve(req.record_ids)
    return BatchStatusUpdateResponse(updated_count=count)


@router.post("/golden-datasets/batch-reject", response_model=BatchStatusUpdateResponse)
async def batch_reject(
    project_id: str,
    req: BatchStatusUpdateRequest,
    container: Container = Depends(get_container),
):
    count = await container.golden_dataset_usecase.batch_reject(req.record_ids)
    return BatchStatusUpdateResponse(updated_count=count)


@router.post("/golden-datasets/import", response_model=ImportGoldenDatasetResponse)
async def import_golden_dataset(
    project_id: str,
    file: UploadFile = File(...),
    container: Container = Depends(get_container),
):
    """上传 JSONL/CSV 文件批量导入黄金记录"""
    filename = file.filename or ""

    if not filename.endswith(".jsonl") and not filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="仅支持 .jsonl 和 .csv 格式")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="文件内容为空")

    # 尝试 UTF-8 解码，失败后尝试 GBK
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = content.decode("gbk")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="文件编码不支持，请使用 UTF-8 或 GBK")

    # 解析文件
    records: list[dict] = []
    try:
        if filename.endswith(".jsonl"):
            records = _parse_jsonl(text)
        else:
            records = _parse_csv(text)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件解析失败: {str(e)}")

    if not records:
        raise HTTPException(status_code=400, detail="文件内容为空")

    if len(records) > MAX_IMPORT_ROWS:
        raise HTTPException(status_code=400, detail=f"单次导入不能超过 {MAX_IMPORT_ROWS} 条")

    result = await container.golden_dataset_usecase.import_records(project_id, records)

    return ImportGoldenDatasetResponse(
        success_count=result.success_count,
        skipped_count=result.skipped_count,
        skipped=[SkippedRecordResponse(row=s.row, reason=s.reason) for s in result.skipped],
    )


def _parse_jsonl(text: str) -> list[dict]:
    """解析 JSONL 格式"""
    records = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        records.append(json.loads(line))
    return records


def _parse_csv(text: str) -> list[dict]:
    """解析 CSV 格式，ground_truth_chunks 用分号分隔"""
    reader = csv.DictReader(io.StringIO(text))
    records = []
    for row in reader:
        gt_raw = row.get("ground_truth_chunks", "")
        gt_chunks = [c.strip() for c in gt_raw.split(";") if c.strip()] if gt_raw else []
        records.append({
            "query": row.get("query", ""),
            "ground_truth_chunks": gt_chunks,
            "reference_answer": row.get("reference_answer", ""),
            "metadata": json.loads(row["metadata"]) if row.get("metadata") else {},
        })
    return records
