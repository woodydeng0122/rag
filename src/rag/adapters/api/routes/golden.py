import csv
import io
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from rag.adapters.api.dependencies import get_current_user
from rag.adapters.api.presenters.golden import GoldenPresenter
from rag.adapters.api.schemas.golden import (
    CreateGoldenRequest,
    UpdateGoldenRequest,
    ImportGoldenResponse,
    SkippedRecordResponse,
    CreateRetrievalRequest,
    RetrievalItemResponse,
    RetrievalResponse,
)
from rag.bootstrap.container import Container, get_container
from rag.domain.entities.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects/{project_id}", tags=["golden"])

MAX_IMPORT_ROWS = 1000


@router.get("/golden")
async def list_goldens(
    project_id: str,
    current_user: User = Depends(get_current_user),
    status: str | None = None,
    retrieval_status: str | None = None,
    container: Container = Depends(get_container),
):
    records = await container.golden_usecase.list_by_project(project_id, status=status, retrieval_status=retrieval_status)
    # 批量查询检索命中摘要
    record_ids = [r.id for r in records]
    summaries = await container.golden_retrieve_usecase.get_retrieval_summaries(record_ids)
    return [GoldenPresenter.to_response(
        r,
        has_retrieval=r.id in summaries,
        retrieval_hit_count=summaries[r.id].hit_count if r.id in summaries else None,
        retrieval_gt_total=summaries[r.id].gt_total if r.id in summaries else None,
    ) for r in records]


@router.get("/documents/{document_id}/golden")
async def list_goldens_by_document(
    project_id: str,
    document_id: str,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
):
    """按文档 ID 查询关联的黄金记录"""
    records = await container.golden_usecase.list_by_document(project_id, document_id)
    return [GoldenPresenter.to_response(r) for r in records]


@router.post("/golden")
async def create_golden(
    project_id: str,
    req: CreateGoldenRequest,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
):
    record = await container.golden_usecase.create(
        project_id=project_id,
        query=req.query,
        ground_truth_chunks=req.ground_truth_chunks,
        reference_answer=req.reference_answer,
    )
    return GoldenPresenter.to_response(record)


@router.patch("/golden/{record_id}")
async def update_golden(
    project_id: str,
    record_id: str,
    req: UpdateGoldenRequest,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
):
    try:
        # 先获取当前记录，用请求中的非 None 字段覆盖
        current = await container.golden_usecase.get(record_id)
        if current is None:
            raise ValueError(f"黄金记录 {record_id} 不存在")
        record = await container.golden_usecase.update(
            record_id=record_id,
            query=req.query if req.query is not None else current.query,
            ground_truth_chunks=req.ground_truth_chunks if req.ground_truth_chunks is not None else current.ground_truth_chunks,
            reference_answer=req.reference_answer if req.reference_answer is not None else current.reference_answer,
            status=req.status,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return GoldenPresenter.to_response(record)


@router.delete("/golden/{record_id}")
async def delete_golden(
    project_id: str,
    record_id: str,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
):
    deleted = await container.golden_usecase.delete(record_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="黄金记录不存在")
    return {"detail": "删除成功"}


@router.post("/golden/{record_id}/retrieval", response_model=RetrievalResponse)
async def create_retrieval(
    project_id: str,
    record_id: str,
    req: CreateRetrievalRequest,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
):
    """触发检索 — 根据黄金记录的 query 执行语义检索，覆盖旧结果"""
    try:
        result = await container.golden_retrieve_usecase.execute(
            record_id=record_id, max_k=req.max_k
        )
    except ValueError as e:
        raise HTTPException(status_code=400 if "嵌入模型" in str(e) else 404, detail=str(e))
    return _retrieval_result_to_response(result)


@router.get("/golden/{record_id}/retrieval", response_model=RetrievalResponse)
async def get_retrieval(
    project_id: str,
    record_id: str,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
):
    """获取检索结果 — 含 chunk 内容和 GT 命中标记"""
    try:
        result = await container.golden_retrieve_usecase.get_retrieval(record_id=record_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _retrieval_result_to_response(result)


@router.post("/golden/import", response_model=ImportGoldenResponse)
async def import_golden(
    project_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
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

    result = await container.golden_usecase.import_records(project_id, records)

    return ImportGoldenResponse(
        success_count=result.success_count,
        skipped_count=result.skipped_count,
        skipped=[SkippedRecordResponse(row=s.row, reason=s.reason) for s in result.skipped],
    )


def _parse_jsonl(text: str) -> list[dict]:
    """解析 JSONL 或 JSON 数组格式，兼容缺少换行分隔的 JSONL"""
    stripped = text.strip()
    if not stripped:
        return []

    # 兼容 JSON 数组格式: [{...}, {...}]
    if stripped.startswith("["):
        try:
            data = json.loads(stripped)
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass  # 不是合法 JSON 数组，回退到逐对象解析

    # 逐对象解析，兼容行内缺少换行分隔的情况
    decoder = json.JSONDecoder()
    records = []
    idx = 0
    while idx < len(stripped):
        # 跳过空白字符
        while idx < len(stripped) and stripped[idx] in " \t\n\r":
            idx += 1
        if idx >= len(stripped):
            break
        try:
            obj, end = decoder.raw_decode(stripped, idx)
            records.append(obj)
            idx = end
        except json.JSONDecodeError:
            # 无法解析，跳过当前行尝试下一行
            next_nl = stripped.find("\n", idx)
            if next_nl == -1:
                break
            idx = next_nl + 1
    return records


def _retrieval_result_to_response(result) -> RetrievalResponse:
    """GoldenRetrievalResult → RetrievalResponse"""
    return RetrievalResponse(
        id=result.id,
        golden_id=result.golden_id,
        max_k=result.max_k,
        latency_ms=result.latency_ms,
        embed_latency_ms=getattr(result, "embed_latency_ms", 0),
        search_latency_ms=getattr(result, "search_latency_ms", 0),
        load_embeddings_latency_ms=getattr(result, "load_embeddings_latency_ms", 0),
        load_project_latency_ms=getattr(result, "load_project_latency_ms", 0),
        load_embed_model_latency_ms=getattr(result, "load_embed_model_latency_ms", 0),
        get_embedder_latency_ms=getattr(result, "get_embedder_latency_ms", 0),
        build_matrix_latency_ms=getattr(result, "build_matrix_latency_ms", 0),
        embed_model_name=result.embed_model_name,
        created_at=result.created_at,
        items=[
            RetrievalItemResponse(
                chunk_id=item.chunk_id,
                score=item.score,
                rank=item.rank,
                content=item.content,
                heading=item.heading,
                source_file=item.source_file,
                file_type=item.file_type,
                is_ground_truth=item.is_ground_truth,
            )
            for item in result.items
        ],
    )


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
