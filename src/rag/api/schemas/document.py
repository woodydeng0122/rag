from pydantic import BaseModel

from rag.domain.entities.document import DocumentStatus, SplitterConfig


class SplitterConfigSchema(BaseModel):
    strategy: str = "section_heading"
    chunk_size: int = 500
    chunk_overlap: int = 50
    min_chars: int = 200
    max_chars: int = 2000


class DocumentResponse(BaseModel):
    id: str
    project_id: str
    filename: str
    storage_key: str
    file_size: int
    file_type: str
    checksum: str
    status: DocumentStatus
    splitter_config: SplitterConfigSchema
    chunk_count: int = 0
    error_message: str = ""
    created_at: str = ""
    updated_at: str = ""


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]


class ProcessDocumentResponse(BaseModel):
    id: str
    status: str
    chunk_count: int
    error_message: str = ""


class BatchProcessRequest(BaseModel):
    document_ids: list[str]


class BatchProcessItem(BaseModel):
    id: str
    status: str
    chunk_count: int = 0
    error_message: str = ""


class BatchProcessResponse(BaseModel):
    total: int
    success: int
    failed: int
    results: list[BatchProcessItem]


class ChunkResponse(BaseModel):
    id: str
    index: int
    heading: str = ""
    content: str
    source_file: str = ""
    file_type: str = ""


class ChunkListResponse(BaseModel):
    document_id: str
    total: int
    chunks: list[ChunkResponse]


class SourceContentResponse(BaseModel):
    document_id: str
    file_type: str
    content: str


class EmbeddingResponse(BaseModel):
    chunk_id: str
    vector: list[float]
    dimension: int
    embedder_model: str = ""
