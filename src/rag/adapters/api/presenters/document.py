from rag.adapters.api.schemas.document import (
    BatchProcessItem,
    BatchProcessResponse,
    ChunkListResponse,
    ChunkResponse,
    DocumentResponse,
    DocumentStatusEnum,
    EmbeddingResponse,
    ProcessDocumentResponse,
    SourceContentResponse,
    SplitterConfigSchema,
)
from rag.adapters.api.schemas.upload import UploadResponse
from rag.application.results.document_result import DocumentWithGoldenCount
from rag.application.results.batch_process_result import BatchProcessResult, ChunksWithDoc, SourceContentWithDoc
from rag.domain.entities.chunk import Chunk
from rag.domain.entities.document import Document, DocumentStatus
from rag.domain.entities.embedding import Embedding

# 领域枚举 → API 枚举映射
_DOMAIN_TO_API_STATUS = {
    DocumentStatus.UPLOADED: DocumentStatusEnum.UPLOADED,
    DocumentStatus.CHUNKING: DocumentStatusEnum.CHUNKING,
    DocumentStatus.CHUNKED: DocumentStatusEnum.CHUNKED,
    DocumentStatus.EMBEDDING: DocumentStatusEnum.EMBEDDING,
    DocumentStatus.EMBEDDED: DocumentStatusEnum.EMBEDDED,
    DocumentStatus.READY: DocumentStatusEnum.READY,
    DocumentStatus.ERROR: DocumentStatusEnum.ERROR,
}


def _to_api_status(status: DocumentStatus) -> DocumentStatusEnum:
    return _DOMAIN_TO_API_STATUS[status]


class DocumentPresenter:
    """文档领域实体 → API 响应转换"""

    @staticmethod
    def to_document_response(r: DocumentWithGoldenCount) -> DocumentResponse:
        d = r.document
        cfg = d.splitter_config
        return DocumentResponse(
            id=d.id,
            project_id=d.project_id,
            filename=d.filename,
            storage_key=d.storage_key,
            file_size=d.file_size,
            file_type=d.file_type,
            checksum=d.checksum,
            status=_to_api_status(d.status),
            splitter_config=SplitterConfigSchema(
                strategy=cfg.strategy,
                chunk_size=cfg.chunk_size,
                chunk_overlap=cfg.chunk_overlap,
                min_chars=cfg.min_chars,
                max_chars=cfg.max_chars,
            ),
            chunk_count=d.chunk_count,
            golden_record_count=r.golden_count,
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
                    "status": _to_api_status(d.status),
                }
                for d in documents
            ],
            count=len(documents),
        )

    @staticmethod
    def to_process_response(d: Document) -> ProcessDocumentResponse:
        return ProcessDocumentResponse(
            id=d.id,
            status=_to_api_status(d.status),
            chunk_count=d.chunk_count,
            error_message=d.error_message,
        )

    @staticmethod
    def to_batch_response(result: BatchProcessResult) -> BatchProcessResponse:
        return BatchProcessResponse(
            total=result.total,
            success=result.success,
            failed=result.failed,
            results=[
                BatchProcessItem(
                    id=item.id,
                    status=DocumentStatusEnum(item.status),
                    chunk_count=item.chunk_count,
                    error_message=item.error_message,
                )
                for item in result.results
            ],
        )

    @staticmethod
    def to_chunk_list_response(
        data: ChunksWithDoc | list[Chunk],
        document_id: str = "",
        file_type: str = "",
        truncate: bool = False,
    ) -> ChunkListResponse:
        if isinstance(data, ChunksWithDoc):
            chunks = data.chunks
            doc_id = data.document_id
            ftype = data.file_type
        else:
            chunks = data
            doc_id = document_id
            ftype = file_type

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
                    file_type=ftype,
                )
            )
        return ChunkListResponse(
            document_id=doc_id,
            total=len(chunk_responses),
            chunks=chunk_responses,
        )

    @staticmethod
    def to_source_content_response(data: SourceContentWithDoc | str, **kwargs) -> SourceContentResponse:
        if isinstance(data, SourceContentWithDoc):
            return SourceContentResponse(
                document_id=data.document_id,
                file_type=data.file_type,
                content=data.content,
            )
        return SourceContentResponse(
            document_id=kwargs.get("document_id", ""),
            file_type=kwargs.get("file_type", ""),
            content=data,
        )

    @staticmethod
    def to_embedding_response(embedding: Embedding) -> EmbeddingResponse:
        return EmbeddingResponse(
            chunk_id=embedding.chunk_id,
            vector=embedding.vector,
            dimension=embedding.dimension,
            embedder_model=embedding.embedder_model,
        )
