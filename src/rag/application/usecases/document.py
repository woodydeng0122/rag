from rag.domain.entities.chunk import Chunk
from rag.domain.entities.document import Document
from rag.domain.entities.embedding import Embedding
from rag.domain.ports.document_repository import DocumentRepositoryPort
from rag.domain.ports.chunk_repository import ChunkRepositoryPort
from rag.domain.ports.embedding_repository import EmbeddingRepositoryPort
from rag.domain.ports.file_storage import FileStoragePort


class DocumentUseCase:
    """文档查询用例 — 列表、删除、查看分块、查看嵌入、读取源文件"""

    def __init__(
        self,
        document_repo: DocumentRepositoryPort,
        chunk_repo: ChunkRepositoryPort,
        embedding_repo: EmbeddingRepositoryPort,
        file_storage: FileStoragePort,
    ):
        self._document_repo = document_repo
        self._chunk_repo = chunk_repo
        self._embedding_repo = embedding_repo
        self._file_storage = file_storage

    async def list_by_project(self, project_id: str) -> list[Document]:
        return await self._document_repo.list_by_project(project_id)

    async def get(self, document_id: str) -> Document | None:
        return await self._document_repo.get_by_id(document_id)

    async def delete(self, document_id: str) -> bool:
        existing = await self._document_repo.get_by_id(document_id)
        if existing is None:
            raise ValueError(f"文档 {document_id} 不存在")
        return await self._document_repo.delete(document_id)

    async def list_chunks(self, document_id: str) -> list[Chunk]:
        doc = await self._document_repo.get_by_id(document_id)
        if doc is None:
            raise ValueError(f"文档 {document_id} 不存在")
        return await self._chunk_repo.list_by_document(document_id)

    async def list_chunks_by_project(self, project_id: str, limit: int = 20, offset: int = 0) -> list[Chunk]:
        return await self._chunk_repo.list_by_project(project_id, limit, offset)

    async def search_chunks_by_project(self, project_id: str, query: str, limit: int = 20, offset: int = 0) -> list[Chunk]:
        return await self._chunk_repo.search_by_project(project_id, query, limit, offset)

    async def get_embedding(self, chunk_id: str) -> Embedding | None:
        return await self._embedding_repo.get_by_chunk_id(chunk_id)

    async def get_source_content(self, document_id: str) -> str:
        """读取文档源文件内容（仅支持文本类型）"""
        doc = await self._document_repo.get_by_id(document_id)
        if doc is None:
            raise ValueError(f"文档 {document_id} 不存在")
        if doc.file_type == "pdf":
            raise ValueError("PDF 文件不支持源文件预览")
        if not self._file_storage.exists(doc.file_path):
            raise FileNotFoundError(f"源文件不存在: {doc.file_path}")
        return self._file_storage.read_text(doc.file_path)
