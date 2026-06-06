import csv
import io
import json

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from rag.api.schemas.golden_dataset import (
    CreateGoldenDatasetRequest,
    UpdateGoldenDatasetRequest,
    GoldenDatasetResponse,
    ImportGoldenDatasetResponse,
    SkippedRecordResponse,
    GenerateGoldenRequest,
    GenerateGoldenResponse,
    GenerationTaskResponse,
    BatchStatusUpdateRequest,
    BatchStatusUpdateResponse,
)
from rag.domain.entities.generate_config import GenerateConfig
from rag.bootstrap.container import Container, get_container

router = APIRouter(prefix="/api/projects/{project_id}", tags=["golden-datasets"])

MAX_IMPORT_ROWS = 1000


def _record_to_response(r) -> GoldenDatasetResponse:
    return GoldenDatasetResponse(
        id=r.id,
        project_id=r.project_id,
        query=r.query,
        ground_truth_chunks=r.ground_truth_chunks,
        reference_answer=r.reference_answer or "",
        status=r.status,
        retrieved_chunk_ids=r.retrieved_chunk_ids or [],
        is_hit=r.is_hit,
        hit_rank=r.hit_rank,
        evaluated_at=r.evaluated_at.isoformat() if r.evaluated_at else None,
        created_at=r.created_at.isoformat() if r.created_at else "",
        metadata=r.metadata if r.metadata else {},
    )


def _task_to_response(t) -> GenerationTaskResponse:
    return GenerationTaskResponse(
        id=t.id,
        project_id=t.project_id,
        status=t.status,
        total=t.total,
        completed=t.completed,
        failed=t.failed,
        document_ids=t.document_ids or [],
        chunk_ids=t.chunk_ids or [],
        config=t.config or {},
        error_message=t.error_message or "",
        created_at=t.created_at.isoformat() if t.created_at else "",
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
            question_types=req.config.question_types or config.question_types,
            difficulty=req.config.difficulty,
            user_persona=req.config.user_persona,
            chunk_batch_size=req.config.chunk_batch_size,
            file_char_threshold=req.config.file_char_threshold,
        )

    try:
        task = await container.generate_golden_usecase.execute(
            project_id=project_id,
            document_ids=req.document_ids or None,
            chunk_ids=req.chunk_ids or None,
            config=config,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return GenerateGoldenResponse(task_id=task.id, status=task.status)


@router.get("/generation-tasks", response_model=list[GenerationTaskResponse])
async def list_generation_tasks(
    project_id: str,
    container: Container = Depends(get_container),
):
    tasks = await container.generate_golden_usecase.task_repo.list_by_project(project_id)
    return [_task_to_response(t) for t in tasks]


@router.get("/generation-tasks/{task_id}", response_model=GenerationTaskResponse)
async def get_generation_task(
    project_id: str,
    task_id: str,
    container: Container = Depends(get_container),
):
    task = await container.generate_golden_usecase.task_repo.get_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="生成任务不存在")
    return _task_to_response(task)


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
