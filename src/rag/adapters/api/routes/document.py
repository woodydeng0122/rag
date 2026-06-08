from fastapi import APIRouter, Depends, HTTPException

from rag.adapters.api.presenters.document import DocumentPresenter
from rag.adapters.api.presenters.golden import GoldenPresenter
from rag.adapters.api.schemas.document import BatchProcessRequest
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
    results = await container.document_usecase.list_with_golden_counts(project_id)
    return [DocumentPresenter.to_document_response(r) for r in results]


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
        result = await container.document_usecase.get_chunks_with_doc(document_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return DocumentPresenter.to_chunk_list_response(result)


@router.get("/documents/{document_id}/source")
async def get_source_content(
    document_id: str,
    container: Container = Depends(get_container),
):
    """获取文档源文件内容（仅支持文本类型）"""
    try:
        result = await container.document_usecase.get_source_content_with_doc(document_id)
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

    return DocumentPresenter.to_source_content_response(result)


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
    records = await container.golden_usecase.list_by_chunk_id(chunk_id, project_id)
    return [GoldenPresenter.to_response(r) for r in records]


@router.post("/documents/batch-process")
async def batch_process_documents(
    req: BatchProcessRequest,
    container: Container = Depends(get_container),
):
    """批量处理文档：对每个 document_id 依次执行处理"""
    result = await container.batch_process_usecase.execute(req.document_ids)
    return DocumentPresenter.to_batch_response(result)
