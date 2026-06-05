from fastapi import APIRouter, Depends, HTTPException

from rag.api.schemas.document import DocumentResponse, DocumentListResponse, ProcessDocumentResponse, BatchProcessRequest, BatchProcessResponse, BatchProcessItem, ChunkResponse, ChunkListResponse, SourceContentResponse, EmbeddingResponse
from rag.bootstrap.container import Container, get_container
from rag.shared.logger import logger

router = APIRouter(prefix="/api", tags=["documents"])


def _doc_to_response(d) -> DocumentResponse:
    return DocumentResponse(
        id=d.id,
        project_id=d.project_id,
        filename=d.filename,
        file_path=d.file_path,
        file_size=d.file_size,
        file_type=d.file_type,
        checksum=d.checksum,
        status=d.status,
        embedder_model=d.embedder_model,
        splitter_strategy=d.splitter_strategy,
        chunk_size=d.chunk_size,
        chunk_overlap=d.chunk_overlap,
        splitter_min_chars=d.splitter_min_chars,
        splitter_max_chars=d.splitter_max_chars,
        chunk_count=d.chunk_count,
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
    documents = await container.document_repo.list_by_project(project_id)
    return [_doc_to_response(d) for d in documents]


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    container: Container = Depends(get_container),
):
    existing = await container.document_repo.get_by_id(document_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="文档不存在")

    deleted = await container.document_repo.delete(document_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="删除失败")
    return {"detail": "删除成功"}


@router.get("/documents/{document_id}/chunks", response_model=ChunkListResponse)
async def list_chunks(
    document_id: str,
    container: Container = Depends(get_container),
):
    """获取文档的分块列表"""
    doc = await container.document_repo.get_by_id(document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")

    chunks = await container.chunk_repo.list_by_document(document_id)
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
                file_type=doc.file_type,
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
    logger.info("get_source_content called", extra={"document_id": document_id})

    doc = await container.document_repo.get_by_id(document_id)
    if doc is None:
        logger.warning("document not found", extra={"document_id": document_id})
        raise HTTPException(status_code=404, detail="文档不存在")

    logger.info("document found", extra={
        "document_id": document_id,
        "file_type": doc.file_type,
        "file_path": doc.file_path,
    })

    if doc.file_type == "pdf":
        raise HTTPException(status_code=400, detail="PDF 文件不支持源文件预览")

    try:
        from pathlib import Path
        file_path = Path(doc.file_path)
        if not file_path.exists():
            logger.warning("source file not found on disk", extra={"file_path": str(file_path)})
            raise HTTPException(status_code=404, detail="源文件不存在")
        content = file_path.read_text(encoding="utf-8")
        logger.info("source file read success", extra={
            "document_id": document_id,
            "content_length": len(content),
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error("failed to read source file", extra={
            "document_id": document_id,
            "file_path": doc.file_path,
            "error": str(e),
        })
        raise HTTPException(status_code=500, detail=f"读取文件失败: {e}")

    return SourceContentResponse(
        document_id=document_id,
        file_type=doc.file_type,
        content=content,
    )


@router.get("/chunks/{chunk_id}/embedding", response_model=EmbeddingResponse)
async def get_chunk_embedding(
    chunk_id: str,
    container: Container = Depends(get_container),
):
    """获取分块的 embedding 向量"""
    embedding = await container.embedding_repo.get_by_chunk_id(chunk_id)
    if embedding is None:
        raise HTTPException(status_code=404, detail="该分块暂无 embedding 数据")
    return EmbeddingResponse(
        chunk_id=embedding.chunk_id,
        vector=embedding.vector,
        dimension=len(embedding.vector),
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
        chunks = await container.chunk_repo.search_by_project(project_id, q, limit, offset)
    else:
        chunks = await container.chunk_repo.list_by_project(project_id, limit, offset)
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
                status="error",
                error_message=str(e),
            ))
            failed_count += 1

    return BatchProcessResponse(
        total=len(req.document_ids),
        success=success_count,
        failed=failed_count,
        results=results,
    )
