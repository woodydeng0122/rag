from dataclasses import dataclass, field

from rag.application.usecases.chunk_and_embed import ChunkAndEmbedUseCase
from rag.application.usecases.ask import AskUseCase
from rag.application.usecases.retrieve import RetrieveUseCase
from rag.application.usecases.evaluate import EvaluateUseCase
from rag.application.usecases.upload import UploadUseCase
from rag.application.usecases.process_document import ProcessDocumentUseCase
from rag.domain.ports.project_repository import ProjectRepositoryPort
from rag.domain.ports.document_repository import DocumentRepositoryPort
from rag.domain.ports.chunk_repository import ChunkRepositoryPort
from rag.domain.ports.embedding_repository import EmbeddingRepositoryPort
from rag.infra.repositories.pg_project_repository import PgProjectRepository
from rag.infra.repositories.pg_document_repository import PgDocumentRepository
from rag.infra.repositories.pg_chunk_repository import PgChunkRepository
from rag.infra.repositories.pg_embedding_repository import PgEmbeddingRepository
from rag.infra.repositories.jsonl_chunk_repository import JsonlChunkRepository
from rag.infra.repositories.jsonl_embedding_repository import JsonlEmbeddingRepository
from rag.infra.embedder.sentence_transformer import SentenceTransformerEmbedder
from rag.infra.retriever.cosine_retriever import CosineRetriever
from rag.infra.llm.dashscope_llm import DashScopeLLM
from rag.infra.loader.file_document_loader import FileDocumentLoader
from rag.infra.splitter.section_heading_splitter import SectionHeadingSplitter
from rag.bootstrap.settings import Settings


@dataclass
class Container:
    """组合根容器 — 持有所有用例实例和配置"""
    # 新增用例
    upload_usecase: UploadUseCase
    process_document_usecase: ProcessDocumentUseCase
    # PG 仓储
    project_repo: ProjectRepositoryPort
    document_repo: DocumentRepositoryPort
    chunk_repo: ChunkRepositoryPort
    # 原有用例
    chunk_and_embed: ChunkAndEmbedUseCase
    ask: AskUseCase
    retrieve: RetrieveUseCase
    evaluate: EvaluateUseCase
    settings: Settings


# 模块级单例
_container: Container | None = None


def build_container(settings: Settings | None = None) -> Container:
    """组合根 — 唯一知道具体实现的地方"""

    if settings is None:
        settings = Settings.from_env()

    # PG 仓储（新增）
    pg_project_repo = PgProjectRepository()
    pg_document_repo = PgDocumentRepository()
    pg_chunk_repo = PgChunkRepository()
    pg_embedding_repo = PgEmbeddingRepository()

    # JSONL 仓储（原有，保留兼容）
    jsonl_chunk_repo = JsonlChunkRepository()
    jsonl_embedding_repo = JsonlEmbeddingRepository()

    # 基础设施适配器
    embedder = SentenceTransformerEmbedder(settings.embedder_model)
    loader = FileDocumentLoader()
    splitter = SectionHeadingSplitter(
        min_chars=settings.splitter_min_chars,
        max_chars=settings.splitter_max_chars,
    )
    llm = DashScopeLLM(
        api_key=settings.dashscope_api_key,
        base_url=settings.dashscope_base_url,
        model=settings.dashscope_model,
    )
    retriever = CosineRetriever(
        embedder=embedder,
        embedding_repo=jsonl_embedding_repo,
        embedding_file=settings.embedding_file,
    )

    # 新增用例组装
    upload_usecase = UploadUseCase(document_repo=pg_document_repo)
    process_document_usecase = ProcessDocumentUseCase(
        document_repo=pg_document_repo,
        chunk_repo=pg_chunk_repo,
        embedding_repo=pg_embedding_repo,
        loader=loader,
        splitter=splitter,
        embedder=embedder,
    )

    # 原有用例组装
    chunk_and_embed = ChunkAndEmbedUseCase(
        loader=loader,
        splitter=splitter,
        embedder=embedder,
        chunk_repo=jsonl_chunk_repo,
        embedding_repo=jsonl_embedding_repo,
    )
    ask = AskUseCase(
        retriever=retriever,
        chunk_repo=jsonl_chunk_repo,
        llm=llm,
        chunk_file=settings.chunk_file,
    )
    retrieve = RetrieveUseCase(
        retriever=retriever,
        chunk_repo=jsonl_chunk_repo,
        chunk_file=settings.chunk_file,
    )
    evaluate = EvaluateUseCase(
        retriever=retriever,
        embedding_file=settings.embedding_file,
        golden_file=settings.golden_file,
        embedder_model=settings.embedder_model,
    )

    return Container(
        upload_usecase=upload_usecase,
        process_document_usecase=process_document_usecase,
        project_repo=pg_project_repo,
        document_repo=pg_document_repo,
        chunk_repo=pg_chunk_repo,
        chunk_and_embed=chunk_and_embed,
        ask=ask,
        retrieve=retrieve,
        evaluate=evaluate,
        settings=settings,
    )


def get_container() -> Container:
    """FastAPI 依赖注入用 — 获取或创建容器"""
    global _container
    if _container is None:
        _container = build_container()
    return _container
