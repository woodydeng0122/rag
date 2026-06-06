from rag.domain.entities.chunk import Chunk
from rag.domain.entities.document import Document
from rag.domain.ports.document_repository import DocumentRepositoryPort
from rag.domain.ports.chunk_repository import ChunkRepositoryPort
from rag.domain.ports.embedding_repository import EmbeddingRepositoryPort
from rag.domain.ports.file_loader import FileLoaderPort
from rag.domain.ports.splitter import SplitterPort
from rag.domain.ports.project_repository import ProjectRepositoryPort
from rag.domain.ports.embed_model_repository import EmbedModelRepositoryPort
from rag.domain.ports.embedder_pool import EmbedderPoolPort


class ProcessDocumentUseCase:
    """文档处理用例 — 手动触发分块+嵌入，从项目读取模型配置"""

    def __init__(
        self,
        document_repo: DocumentRepositoryPort,
        chunk_repo: ChunkRepositoryPort,
        embedding_repo: EmbeddingRepositoryPort,
        project_repo: ProjectRepositoryPort,
        embed_model_repo: EmbedModelRepositoryPort,
        loader: FileLoaderPort,
        splitter: SplitterPort,
        embedder_pool: EmbedderPoolPort,
    ):
        self._document_repo = document_repo
        self._chunk_repo = chunk_repo
        self._embedding_repo = embedding_repo
        self._project_repo = project_repo
        self._embed_model_repo = embed_model_repo
        self._loader = loader
        self._splitter = splitter
        self._embedder_pool = embedder_pool

    async def execute(self, document_id: str) -> Document:
        # 1. 获取文档
        doc = await self._document_repo.get_by_id(document_id)
        if doc is None:
            raise ValueError(f"文档不存在: {document_id}")
        if doc.status not in ("uploaded", "error", "chunking", "embedding"):
            raise ValueError(f"文档状态不允许处理: {doc.status}，仅 uploaded / error / chunking / embedding 可处理")

        # 2. 从项目获取嵌入模型
        project = await self._project_repo.get_by_id(doc.project_id)
        if project is None:
            raise ValueError(f"项目不存在: {doc.project_id}")

        embed_model = await self._embed_model_repo.get_by_id(project.embed_model_id)
        if embed_model is None:
            raise ValueError(f"嵌入模型不存在: {project.embed_model_id}")
        if not embed_model.is_online:
            raise ValueError(f"嵌入模型不可用: {embed_model.name} (status={embed_model.status.value})")

        embedder = self._embedder_pool.get(embed_model.name)

        try:
            # 3. 加载文档文本
            text = self._load_text(doc)

            # 4. 分块
            await self._document_repo.update_status(document_id, "chunking")
            chunks = self._splitter.split(text, **self._build_splitter_kwargs(doc))

            for i, chunk in enumerate(chunks):
                chunk.id = f"{document_id}_chunk_{i}"
                chunk.index = i
                chunk.source_file = doc.file_path

            await self._chunk_repo.save_batch(chunks, document_id=document_id)
            await self._document_repo.update_status(document_id, "chunked")
            await self._document_repo.update_chunk_count(document_id, len(chunks))

            # 5. 嵌入
            await self._document_repo.update_status(document_id, "embedding")
            texts = [c.content for c in chunks]
            vectors = embedder.embed(texts)

            # 6. 保存嵌入
            from rag.domain.entities.embedding import Embedding
            embeddings = [
                Embedding(chunk_id=c.id, vector=v)
                for c, v in zip(chunks, vectors)
            ]
            await self._embedding_repo.save_batch(embeddings, embedder_model=embed_model.name)
            await self._document_repo.update_status(document_id, "embedded")

            # 7. 完成
            await self._document_repo.update_status(document_id, "ready")

        except Exception as e:
            await self._document_repo.update_status(document_id, "error", str(e))
            raise

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
