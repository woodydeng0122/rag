from fastapi import APIRouter, Depends, HTTPException

from rag.api.schemas.document import DocumentResponse, DocumentListResponse, ProcessDocumentResponse, BatchProcessRequest, BatchProcessResponse, BatchProcessItem, ChunkResponse, ChunkListResponse, SourceContentResponse, EmbeddingResponse, SplitterConfigSchema
from rag.api.schemas.golden_dataset import GoldenDatasetResponse, EvaluationMetricsResponse
from rag.bootstrap.container import Container, get_container
from rag.domain.entities.document import DocumentStatus
from rag.shared.logger import logger

router = APIRouter(prefix="/api", tags=["documents"])


def _doc_to_response(d, golden_count: int = 0) -> DocumentResponse:
    cfg = d.splitter_config
    return DocumentResponse(
        id=d.id,
        project_id=d.project_id,
        filename=d.filename,
        storage_key=d.storage_key,
        file_size=d.file_size,
        file_type=d.file_type,
        checksum=d.checksum,
        status=d.status,
        splitter_config=SplitterConfigSchema(
            strategy=cfg.strategy,
            chunk_size=cfg.chunk_size,
            chunk_overlap=cfg.chunk_overlap,
            min_chars=cfg.min_chars,
            max_chars=cfg.max_chars,
        ),
        chunk_count=d.chunk_count,
        golden_record_count=golden_count,
        error_message=d.error_message,
        created_at=d.created_at.isoformat() if d.created_at else "",
        updated_at=d.updated_at.isoformat() if d.updated_at else "",
    )


@router.post("/documents/{document_id}/process", response_model=ProcessDocumentResponse)
async def process_document(
    document_id: str,
    container: Container = Depends(get_container),
):
    try:
        doc = await container.process_document_usecase.execute(document_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return ProcessDocumentResponse(
        id=doc.id,
        status=doc.status,
        chunk_count=doc.chunk_count,
        error_message=doc.error_message,
    )


@router.get("/projects/{project_id}/documents", response_model=list[DocumentResponse])
async def list_documents(
    project_id: str,
    container: Container = Depends(get_container),
):
    documents = await container.document_usecase.list_by_project(project_id)
    doc_ids = [d.id for d in documents]
    golden_counts = await container.golden_dataset_usecase.count_golden_records_by_documents(doc_ids) if doc_ids else {}
    return [_doc_to_response(d, golden_count=golden_counts.get(d.id, 0)) for d in documents]


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    container: Container = Depends(get_container),
):
    try:
        deleted = await container.document_usecase.delete(document_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    if not deleted:
        raise HTTPException(status_code=500, detail="删除失败")
    return {"detail": "删除成功"}


@router.get("/documents/{document_id}/chunks", response_model=ChunkListResponse)
async def list_chunks(
    document_id: str,
    container: Container = Depends(get_container),
):
    """获取文档的分块列表"""
    try:
        chunks = await container.document_usecase.list_chunks(document_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    doc = await container.document_usecase.get(document_id)
    return ChunkListResponse(
        document_id=document_id,
        total=len(chunks),
        chunks=[
            ChunkResponse(
                id=c.id,
                index=c.index,
                heading=c.heading,
                content=c.content,
                source_file=c.source_file,
                file_type=doc.file_type if doc else "",
            )
            for c in chunks
        ],
    )


@router.get("/documents/{document_id}/source", response_model=SourceContentResponse)
async def get_source_content(
    document_id: str,
    container: Container = Depends(get_container),
):
    """获取文档源文件内容（仅支持文本类型）"""
    try:
        content = await container.document_usecase.get_source_content(document_id)
    except ValueError as e:
        if "PDF" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("failed to read source file", extra={
            "document_id": document_id,
            "error": str(e),
        })
        raise HTTPException(status_code=500, detail=f"读取文件失败: {e}")

    doc = await container.document_usecase.get(document_id)
    return SourceContentResponse(
        document_id=document_id,
        file_type=doc.file_type if doc else "",
        content=content,
    )


@router.get("/chunks/{chunk_id}/embedding", response_model=EmbeddingResponse)
async def get_chunk_embedding(
    chunk_id: str,
    container: Container = Depends(get_container),
):
    """获取分块的 embedding 向量"""
    embedding = await container.document_usecase.get_embedding(chunk_id)
    if embedding is None:
        raise HTTPException(status_code=404, detail="该分块暂无 embedding 数据")
    return EmbeddingResponse(
        chunk_id=embedding.chunk_id,
        vector=embedding.vector,
        dimension=embedding.dimension,
        embedder_model=embedding.embedder_model,
    )


@router.get("/projects/{project_id}/chunks/search", response_model=ChunkListResponse)
async def search_chunks_by_project(
    project_id: str,
    q: str = "",
    limit: int = 20,
    offset: int = 0,
    container: Container = Depends(get_container),
):
    """按项目搜索分块内容，支持分页"""
    if q:
        chunks = await container.document_usecase.search_chunks_by_project(project_id, q, limit, offset)
    else:
        chunks = await container.document_usecase.list_chunks_by_project(project_id, limit, offset)
    return ChunkListResponse(
        document_id="",
        total=len(chunks),
        chunks=[
            ChunkResponse(
                id=c.id,
                index=c.index,
                heading=c.heading,
                content=c.content[:200] + "..." if len(c.content) > 200 else c.content,
                source_file=c.source_file,
            )
            for c in chunks
        ],
    )


@router.get("/projects/{project_id}/chunks/{chunk_id}/golden-records", response_model=list[GoldenDatasetResponse])
async def get_chunk_golden_records(
    project_id: str,
    chunk_id: str,
    container: Container = Depends(get_container),
):
    """查询分块关联的黄金记录"""
    records = await container.golden_dataset_usecase.list_by_chunk_id(chunk_id, project_id)
    return [
        GoldenDatasetResponse(
            id=r.id,
            project_id=r.project_id,
            query=r.query,
            ground_truth_chunks=r.ground_truth_chunks,
            reference_answer=r.reference_answer or "",
            status=r.status.value if hasattr(r.status, "value") else r.status,
            evaluation=EvaluationMetricsResponse(
                retrieved_chunk_ids=r.evaluation.retrieved_chunk_ids or [],
                is_hit=r.evaluation.is_hit,
                hit_rank=r.evaluation.hit_rank,
                evaluated_at=r.evaluation.evaluated_at.isoformat() if r.evaluation and r.evaluation.evaluated_at else None,
            ) if r.evaluation else None,
            created_at=r.created_at.isoformat() if r.created_at else "",
            metadata=r.metadata if r.metadata else {},
        )
        for r in records
    ]


@router.post("/documents/batch-process", response_model=BatchProcessResponse)
async def batch_process_documents(
    req: BatchProcessRequest,
    container: Container = Depends(get_container),
):
    """批量处理文档：对每个 document_id 依次执行处理"""
    results: list[BatchProcessItem] = []
    success_count = 0
    failed_count = 0

    for doc_id in req.document_ids:
        try:
            doc = await container.process_document_usecase.execute(doc_id)
            results.append(BatchProcessItem(
                id=doc.id,
                status=doc.status,
                chunk_count=doc.chunk_count,
                error_message=doc.error_message,
            ))
            success_count += 1
        except Exception as e:
            results.append(BatchProcessItem(
                id=doc_id,
                status=DocumentStatus.ERROR,
                error_message=str(e),
            ))
            failed_count += 1

    return BatchProcessResponse(
        total=len(req.document_ids),
        success=success_count,
        failed=failed_count,
        results=results,
    )
