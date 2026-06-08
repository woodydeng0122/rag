from fastapi import APIRouter, Depends, HTTPException

from rag.api.presenters.document import DocumentPresenter
from rag.api.presenters.golden_dataset import GoldenDatasetPresenter
from rag.api.schemas.document import BatchProcessRequest
from rag.bootstrap.container import Container, get_container
from rag.shared.logger import logger

router = APIRouter(prefix="/api", tags=["documents"])


@router.post("/documents/{document_id}/process")
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

    return DocumentPresenter.to_process_response(doc)


@router.get("/projects/{project_id}/documents")
async def list_documents(
    project_id: str,
    container: Container = Depends(get_container),
):
    documents = await container.document_usecase.list_by_project(project_id)
    doc_ids = [d.id for d in documents]
    golden_counts = await container.golden_dataset_usecase.count_golden_records_by_documents(doc_ids) if doc_ids else {}
    return [DocumentPresenter.to_document_response(d, golden_count=golden_counts.get(d.id, 0)) for d in documents]


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


@router.get("/documents/{document_id}/chunks")
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
    return DocumentPresenter.to_chunk_list_response(
        chunks, document_id=document_id, file_type=doc.file_type if doc else ""
    )


@router.get("/documents/{document_id}/source")
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
    return DocumentPresenter.to_source_content_response(
        document_id=document_id,
        file_type=doc.file_type if doc else "",
        content=content,
    )


@router.get("/chunks/{chunk_id}/embedding")
async def get_chunk_embedding(
    chunk_id: str,
    container: Container = Depends(get_container),
):
    """获取分块的 embedding 向量"""
    embedding = await container.document_usecase.get_embedding(chunk_id)
    if embedding is None:
        raise HTTPException(status_code=404, detail="该分块暂无 embedding 数据")
    return DocumentPresenter.to_embedding_response(embedding)


@router.get("/projects/{project_id}/chunks/search")
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
    return DocumentPresenter.to_chunk_list_response(chunks, truncate=True)


@router.get("/projects/{project_id}/chunks/{chunk_id}/golden-records")
async def get_chunk_golden_records(
    project_id: str,
    chunk_id: str,
    container: Container = Depends(get_container),
):
    """查询分块关联的黄金记录"""
    records = await container.golden_dataset_usecase.list_by_chunk_id(chunk_id, project_id)
    return [GoldenDatasetPresenter.to_response(r) for r in records]


@router.post("/documents/batch-process")
async def batch_process_documents(
    req: BatchProcessRequest,
    container: Container = Depends(get_container),
):
    """批量处理文档：对每个 document_id 依次执行处理"""
    results = []
    success_count = 0
    failed_count = 0

    for doc_id in req.document_ids:
        try:
            doc = await container.process_document_usecase.execute(doc_id)
            results.append(DocumentPresenter.to_batch_item(doc))
            success_count += 1
        except Exception as e:
            results.append(DocumentPresenter.to_batch_failed_item(doc_id, str(e)))
            failed_count += 1

    return DocumentPresenter.to_batch_response(
        total=len(req.document_ids),
        success=success_count,
        failed=failed_count,
        results=results,
    )
