from rag.domain.entities.chunk import Chunk
from rag.domain.entities.document import Document
from rag.domain.ports.document_repository import DocumentRepositoryPort
from rag.domain.ports.chunk_repository import ChunkRepositoryPort
from rag.domain.ports.embedding_repository import EmbeddingRepositoryPort
from rag.domain.ports.file_loader import FileLoaderPort
from rag.domain.ports.splitter import SplitterPort
from rag.domain.ports.embedder import EmbedderPort


class ProcessDocumentUseCase:
    """文档处理用例 — 手动触发分块+嵌入，状态流转，结果写入 chunk/embedding 表"""

    def __init__(
        self,
        document_repo: DocumentRepositoryPort,
        chunk_repo: ChunkRepositoryPort,
        embedding_repo: EmbeddingRepositoryPort,
        loader: FileLoaderPort,
        splitter: SplitterPort,
        embedder: EmbedderPort,
    ):
        self._document_repo = document_repo
        self._chunk_repo = chunk_repo
        self._embedding_repo = embedding_repo
        self._loader = loader
        self._splitter = splitter
        self._embedder = embedder

    async def execute(self, document_id: str) -> Document:
        # 1. 获取文档
        doc = await self._document_repo.get_by_id(document_id)
        if doc is None:
            raise ValueError(f"文档不存在: {document_id}")
        if doc.status not in ("uploaded", "error", "chunking", "embedding"):
            raise ValueError(f"文档状态不允许处理: {doc.status}，仅 uploaded / error / chunking / embedding 可处理")

        try:
            # 2. 加载文档文本
            text = self._load_text(doc)

            # 3. 分块
            await self._document_repo.update_status(document_id, "chunking")
            chunks = self._splitter.split(text, **self._build_splitter_kwargs(doc))

            # 为每个 chunk 设置 id 和 document 关联
            for i, chunk in enumerate(chunks):
                chunk.id = f"{document_id}_chunk_{i}"
                chunk.index = i
                chunk.source_file = doc.file_path

            # 保存分块
            await self._chunk_repo.save_batch(chunks, document_id=document_id)
            await self._document_repo.update_status(document_id, "chunked")
            await self._document_repo.update_chunk_count(document_id, len(chunks))

            # 4. 嵌入
            await self._document_repo.update_status(document_id, "embedding")
            texts = [c.content for c in chunks]
            vectors = self._embedder.embed(texts)

            # 5. 保存嵌入
            from rag.domain.entities.embedding import Embedding
            embeddings = [
                Embedding(chunk_id=c.id, vector=v)
                for c, v in zip(chunks, vectors)
            ]
            await self._embedding_repo.save_batch(embeddings, embedder_model=doc.embedder_model)
            await self._document_repo.update_status(document_id, "embedded")

            # 6. 完成
            await self._document_repo.update_status(document_id, "ready")

        except Exception as e:
            await self._document_repo.update_status(document_id, "error", str(e))
            raise

        # 返回最新状态
        return await self._document_repo.get_by_id(document_id)

    def _load_text(self, doc: Document) -> str:
        """根据文件类型加载文本"""
        if doc.file_type == "pdf":
            return self._loader.load_file_pdf(doc.file_path)
        elif doc.file_type in ("md", "txt"):
            return self._loader.load_file_txt(doc.file_path)
        else:
            raise ValueError(f"不支持的文件类型: {doc.file_type}")

    @staticmethod
    def _build_splitter_kwargs(doc: Document) -> dict:
        """根据文档的分块策略构建参数"""
        if doc.splitter_strategy == "fixed":
            return {"chunk_size": doc.chunk_size, "overlap": doc.chunk_overlap}
        elif doc.splitter_strategy == "section_heading":
            return {"min_chars": doc.splitter_min_chars, "max_chars": doc.splitter_max_chars}
        return {}
