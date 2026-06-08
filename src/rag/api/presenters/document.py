from rag.api.schemas.document import (
    BatchProcessItem,
    BatchProcessResponse,
    ChunkListResponse,
    ChunkResponse,
    DocumentResponse,
    EmbeddingResponse,
    ProcessDocumentResponse,
    SourceContentResponse,
    SplitterConfigSchema,
)
from rag.api.schemas.upload import UploadResponse
from rag.domain.entities.chunk import Chunk
from rag.domain.entities.document import Document, DocumentStatus
from rag.domain.entities.embedding import Embedding


class DocumentPresenter:
    """文档领域实体 → API 响应转换"""

    @staticmethod
    def to_document_response(d: Document, golden_count: int = 0) -> DocumentResponse:
        cfg = d.splitter_config
        return DocumentResponse(
            id=d.id,
            project_id=d.project_id,
            filename=d.filename,
            storage_key=d.storage_key,
            file_size=d.file_size,
            file_type=d.file_type,
            checksum=d.checksum,
            status=d.status.value,
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

    @staticmethod
    def to_upload_response(documents: list[Document]) -> UploadResponse:
        return UploadResponse(
            documents=[
                {
                    "id": d.id,
                    "filename": d.filename,
                    "file_type": d.file_type,
                    "file_size": d.file_size,
                    "status": d.status.value,
                }
                for d in documents
            ],
            count=len(documents),
        )

    @staticmethod
    def to_process_response(d: Document) -> ProcessDocumentResponse:
        return ProcessDocumentResponse(
            id=d.id,
            status=d.status.value,
            chunk_count=d.chunk_count,
            error_message=d.error_message,
        )

    @staticmethod
    def to_batch_item(doc: Document) -> BatchProcessItem:
        return BatchProcessItem(
            id=doc.id,
            status=doc.status.value,
            chunk_count=doc.chunk_count,
            error_message=doc.error_message,
        )

    @staticmethod
    def to_batch_failed_item(doc_id: str, error_message: str) -> BatchProcessItem:
        return BatchProcessItem(
            id=doc_id,
            status=DocumentStatus.ERROR.value,
            error_message=error_message,
        )

    @staticmethod
    def to_batch_response(
        total: int, success: int, failed: int, results: list[BatchProcessItem]
    ) -> BatchProcessResponse:
        return BatchProcessResponse(
            total=total,
            success=success,
            failed=failed,
            results=results,
        )

    @staticmethod
    def to_chunk_list_response(
        chunks: list[Chunk],
        document_id: str = "",
        file_type: str = "",
        truncate: bool = False,
    ) -> ChunkListResponse:
        chunk_responses = []
        for c in chunks:
            content = c.content
            if truncate and len(content) > 200:
                content = content[:200] + "..."
            chunk_responses.append(
                ChunkResponse(
                    id=c.id,
                    index=c.index,
                    heading=c.heading,
                    content=content,
                    source_file=c.source_file,
                    file_type=file_type,
                )
            )
        return ChunkListResponse(
            document_id=document_id,
            total=len(chunk_responses),
            chunks=chunk_responses,
        )

    @staticmethod
    def to_source_content_response(
        document_id: str, file_type: str, content: str
    ) -> SourceContentResponse:
        return SourceContentResponse(
            document_id=document_id,
            file_type=file_type,
            content=content,
        )

    @staticmethod
    def to_embedding_response(embedding: Embedding) -> EmbeddingResponse:
        return EmbeddingResponse(
            chunk_id=embedding.chunk_id,
            vector=embedding.vector,
            dimension=embedding.dimension,
            embedder_model=embedding.embedder_model,
        )
