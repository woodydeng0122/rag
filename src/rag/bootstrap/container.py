from dataclasses import dataclass

from rag.application.usecases.ask import AskUseCase
from rag.application.usecases.retrieve import RetrieveUseCase
from rag.application.usecases.evaluate import EvaluateUseCase
from rag.application.usecases.golden_dataset import GoldenDatasetUseCase
from rag.application.usecases.upload import UploadUseCase
from rag.application.usecases.process_document import ProcessDocumentUseCase
from rag.application.usecases.scan_embed_models import ScanEmbedModelsUseCase
from rag.application.usecases.project import ProjectUseCase
from rag.application.usecases.document import DocumentUseCase
from rag.application.usecases.embed_model import EmbedModelUseCase
from rag.application.usecases.profile import ProfileUseCase
from rag.infra.repositories.pg_project_repository import PgProjectRepository
from rag.infra.repositories.pg_document_repository import PgDocumentRepository
from rag.infra.repositories.pg_chunk_repository import PgChunkRepository
from rag.infra.repositories.pg_embedding_repository import PgEmbeddingRepository
from rag.infra.repositories.pg_embed_model_repository import PgEmbedModelRepository
from rag.infra.repositories.pg_golden_dataset_repository import PgGoldenDatasetRepository
from rag.infra.repositories.pg_profile_repository import PgProfileRepository
from rag.infra.embedder.sentence_transformer import SentenceTransformerEmbedder
from rag.infra.embedder.model_scanner import ModelScanner
from rag.infra.embedder.embedder_pool import EmbedderPool
from rag.infra.retriever.cosine_retriever import CosineRetriever
from rag.infra.llm.dashscope_llm import DashScopeLLM
from rag.infra.loader.file_document_loader import FileDocumentLoader
from rag.infra.splitter.section_heading_splitter import SectionHeadingSplitter
from rag.infra.storage.local_file_storage import LocalFileStorage
from rag.bootstrap.settings import Settings


@dataclass
class Container:
    """组合根容器 — 持有所有用例实例和配置"""
    # 用例
    upload_usecase: UploadUseCase
    process_document_usecase: ProcessDocumentUseCase
    golden_dataset_usecase: GoldenDatasetUseCase
    scan_embed_models_usecase: ScanEmbedModelsUseCase
    project_usecase: ProjectUseCase
    document_usecase: DocumentUseCase
    embed_model_usecase: EmbedModelUseCase
    profile_usecase: ProfileUseCase
    ask: AskUseCase
    retrieve: RetrieveUseCase
    evaluate: EvaluateUseCase
    settings: Settings
    # 基础设施
    model_scanner: ModelScanner


# 模块级单例
_container: Container | None = None


def build_container(settings: Settings | None = None) -> Container:
    """组合根 — 唯一知道具体实现的地方"""

    if settings is None:
        settings = Settings.from_env()

    # PG 仓储
    pg_project_repo = PgProjectRepository()
    pg_document_repo = PgDocumentRepository()
    pg_chunk_repo = PgChunkRepository()
    pg_embedding_repo = PgEmbeddingRepository()
    pg_embed_model_repo = PgEmbedModelRepository()
    pg_golden_repo = PgGoldenDatasetRepository()
    pg_profile_repo = PgProfileRepository()

    # 基础设施适配器
    embedder_pool = EmbedderPool(factory=SentenceTransformerEmbedder, max_size=3)
    model_scanner = ModelScanner(models_dir="models")
    file_storage = LocalFileStorage()
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

    # 检索器 — 使用 PG 仓储
    retriever = CosineRetriever(
        embedder_pool=embedder_pool,
        embedding_repo=pg_embedding_repo,
        embed_model_repo=pg_embed_model_repo,
    )

    # 用例组装
    scan_embed_models_usecase = ScanEmbedModelsUseCase(
        embed_model_repo=pg_embed_model_repo,
        model_scanner=model_scanner,
    )
    upload_usecase = UploadUseCase(document_repo=pg_document_repo, file_storage=file_storage)
    process_document_usecase = ProcessDocumentUseCase(
        document_repo=pg_document_repo,
        chunk_repo=pg_chunk_repo,
        embedding_repo=pg_embedding_repo,
        project_repo=pg_project_repo,
        embed_model_repo=pg_embed_model_repo,
        loader=loader,
        splitter=splitter,
        embedder_pool=embedder_pool,
    )
    golden_dataset_usecase = GoldenDatasetUseCase(golden_repo=pg_golden_repo, chunk_repo=pg_chunk_repo)
    project_usecase = ProjectUseCase(
        project_repo=pg_project_repo,
        embed_model_repo=pg_embed_model_repo,
    )
    document_usecase = DocumentUseCase(
        document_repo=pg_document_repo,
        chunk_repo=pg_chunk_repo,
        embedding_repo=pg_embedding_repo,
        file_storage=file_storage,
    )
    embed_model_usecase = EmbedModelUseCase(embed_model_repo=pg_embed_model_repo, project_repo=pg_project_repo, model_scanner=model_scanner)
    profile_usecase = ProfileUseCase(
        profile_repo=pg_profile_repo,
        project_repo=pg_project_repo,
    )
    ask = AskUseCase(
        retriever=retriever,
        chunk_repo=pg_chunk_repo,
        llm=llm,
    )
    retrieve = RetrieveUseCase(
        retriever=retriever,
        chunk_repo=pg_chunk_repo,
    )
    evaluate = EvaluateUseCase(
        retriever=retriever,
        golden_repo=pg_golden_repo,
        project_repo=pg_project_repo,
    )

    return Container(
        upload_usecase=upload_usecase,
        process_document_usecase=process_document_usecase,
        golden_dataset_usecase=golden_dataset_usecase,
        scan_embed_models_usecase=scan_embed_models_usecase,
        project_usecase=project_usecase,
        document_usecase=document_usecase,
        embed_model_usecase=embed_model_usecase,
        profile_usecase=profile_usecase,
        ask=ask,
        retrieve=retrieve,
        evaluate=evaluate,
        settings=settings,
        model_scanner=model_scanner,
    )


def get_container() -> Container:
    """FastAPI 依赖注入用 — 获取或创建容器"""
    global _container
    if _container is None:
        _container = build_container()
    return _container
