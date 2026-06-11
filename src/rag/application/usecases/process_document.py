from rag.domain.entities.chunk import Chunk
from rag.domain.entities.document import Document, DocumentStatus
from rag.domain.entities.embedding import Embedding
from rag.domain.ports.document_repository import DocumentRepositoryPort
from rag.domain.ports.chunk_repository import ChunkRepositoryPort
from rag.domain.ports.embedding_repository import EmbeddingRepositoryPort
from rag.domain.ports.file_loader import FileLoaderPort
from rag.domain.ports.splitter import SplitterPort
from rag.domain.ports.project_repository import ProjectRepositoryPort
from rag.domain.ports.embed_model_repository import EmbedModelRepositoryPort
from rag.domain.ports.embedder_pool import EmbedderPoolPort
from rag.domain.ports.markdown_preprocessor import MarkdownPreprocessorPort


class ProcessDocumentUseCase:
    """文档处理用例 — 手动触发预处理+分块+嵌入，从项目读取模型配置"""

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
        preprocessor: MarkdownPreprocessorPort,
    ):
        self._document_repo = document_repo
        self._chunk_repo = chunk_repo
        self._embedding_repo = embedding_repo
        self._project_repo = project_repo
        self._embed_model_repo = embed_model_repo
        self._loader = loader
        self._splitter = splitter
        self._embedder_pool = embedder_pool
        self._preprocessor = preprocessor

    async def execute(self, document_id: str) -> Document:
        # 1. 获取文档
        doc = await self._document_repo.get_by_id(document_id)
        if doc is None:
            raise ValueError(f"文档不存在: {document_id}")

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

            # 4. 预处理（展开文件包含、剥离锚点等 Markdown 扩展语法）
            if doc.is_text_file:
                text = self._preprocessor.preprocess(text, source_path=doc.storage_key)

            # 5. 分块
            doc.start_chunking()
            await self._document_repo.update_status(document_id, doc.status)
            chunks = self._splitter.split(text, **doc.splitter_config.to_splitter_kwargs())

            for i, chunk in enumerate(chunks):
                chunk.assign_identity(document_id, i, doc.storage_key)

            await self._chunk_repo.save_batch(chunks, document_id=document_id)
            doc.finish_chunking(len(chunks))
            await self._document_repo.update_status(document_id, doc.status)
            await self._document_repo.update_chunk_count(document_id, doc.chunk_count)

            # 6. 嵌入
            doc.start_embedding()
            await self._document_repo.update_status(document_id, doc.status)
            texts = [c.content for c in chunks]
            vectors = embedder.embed(texts)

            # 7. 保存嵌入
            embeddings = [
                Embedding(chunk_id=c.id, vector=v, embedder_model=embed_model.name)
                for c, v in zip(chunks, vectors)
            ]
            await self._embedding_repo.save_batch(embeddings)
            doc.finish_embedding()
            await self._document_repo.update_status(document_id, doc.status)

            # 8. 完成
            doc.mark_ready()
            await self._document_repo.update_status(document_id, doc.status)

        except Exception as e:
            doc.mark_error(str(e))
            await self._document_repo.update_status(document_id, doc.status, doc.error_message)
            raise

        return await self._document_repo.get_by_id(document_id)

    def _load_text(self, doc: Document) -> str:
        """根据文件类型加载文本 — 需要外部 FileLoaderPort，留在 Use Case"""
        if doc.file_type == "pdf":
            return self._loader.load_file_pdf(doc.storage_key)
        elif doc.is_text_file:
            return self._loader.load_file_txt(doc.storage_key)
        else:
            raise ValueError(f"不支持的文件类型: {doc.file_type}")
