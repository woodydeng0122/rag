from rag.application.results.batch_process_result import BatchProcessItem, BatchProcessResult
from rag.domain.entities.document import DocumentStatus
from rag.domain.ports.document_repository import DocumentRepositoryPort
from rag.domain.ports.chunk_repository import ChunkRepositoryPort
from rag.domain.ports.embedding_repository import EmbeddingRepositoryPort
from rag.domain.ports.project_repository import ProjectRepositoryPort
from rag.domain.ports.embed_model_repository import EmbedModelRepositoryPort
from rag.domain.ports.file_loader import FileLoaderPort
from rag.domain.ports.splitter import SplitterPort
from rag.domain.ports.embedder_pool import EmbedderPoolPort


class BatchProcessDocumentUseCase:
    """批量处理文档用例 — 对多个文档依次执行分块+嵌入"""

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

    async def execute(self, document_ids: list[str]) -> BatchProcessResult:
        """批量处理文档，返回汇总结果"""
        results: list[BatchProcessItem] = []
        success_count = 0
        failed_count = 0

        for doc_id in document_ids:
            try:
                doc = await self._process_single(doc_id)
                results.append(BatchProcessItem(
                    id=doc.id,
                    status=doc.status.value,
                    chunk_count=doc.chunk_count,
                ))
                success_count += 1
            except Exception as e:
                results.append(BatchProcessItem(
                    id=doc_id,
                    status=DocumentStatus.ERROR.value,
                    error_message=str(e),
                ))
                failed_count += 1

        return BatchProcessResult(
            total=len(document_ids),
            success=success_count,
            failed=failed_count,
            results=results,
        )

    async def _process_single(self, document_id: str):
        """处理单个文档 — 复用 ProcessDocumentUseCase 的核心逻辑"""
        from rag.application.usecases.process_document import ProcessDocumentUseCase

        # 委托给 ProcessDocumentUseCase，避免重复实现
        usecase = ProcessDocumentUseCase(
            document_repo=self._document_repo,
            chunk_repo=self._chunk_repo,
            embedding_repo=self._embedding_repo,
            project_repo=self._project_repo,
            embed_model_repo=self._embed_model_repo,
            loader=self._loader,
            splitter=self._splitter,
            embedder_pool=self._embedder_pool,
        )
        return await usecase.execute(document_id)
