from __future__ import annotations

from dataclasses import dataclass

from rag.application.usecases.ask import AskUseCase
from rag.application.usecases.auth import AuthUseCase
from rag.application.usecases.batch_process_document import BatchProcessDocumentUseCase
from rag.application.usecases.document import DocumentUseCase
from rag.application.usecases.embed_model import EmbedModelUseCase
from rag.application.usecases.golden import GoldenUseCase
from rag.application.usecases.golden_retrieve import GoldenRetrieveUseCase
from rag.application.usecases.process_document import ProcessDocumentUseCase
from rag.application.usecases.profile import ProfileUseCase
from rag.application.usecases.project import ProjectUseCase
from rag.application.usecases.project_evaluation import ProjectEvaluationUseCase
from rag.application.usecases.qa import QAUseCase
from rag.application.usecases.scan_embed_models import ScanEmbedModelsUseCase
from rag.application.usecases.upload import UploadUseCase
from rag.bootstrap.settings import Settings
from rag.domain.value_objects.retrieval_strategy import RetrievalStrategy
from rag.domain.ports.retriever import RetrieverPort
from rag.infra.embedder.model_scanner import ModelScanner


@dataclass
class Container:
    """组合根容器 — 持有所有用例实例和配置"""

    # 用例
    upload_usecase: UploadUseCase
    process_document_usecase: ProcessDocumentUseCase
    batch_process_usecase: BatchProcessDocumentUseCase
    golden_usecase: GoldenUseCase
    golden_retrieve_usecase: GoldenRetrieveUseCase
    evaluation_usecase: ProjectEvaluationUseCase
    scan_embed_models_usecase: ScanEmbedModelsUseCase
    project_usecase: ProjectUseCase
    document_usecase: DocumentUseCase
    embed_model_usecase: EmbedModelUseCase
    profile_usecase: ProfileUseCase
    auth_usecase: AuthUseCase
    ask: AskUseCase
    qa: QAUseCase
    retrieve: RetrieveUseCase
    settings: Settings
    # 基础设施
    model_scanner: ModelScanner
    # 检索器工厂
    _retrievers: dict[RetrievalStrategy, RetrieverPort] = None  # type: ignore[assignment]

    def get_retriever(self, strategy: RetrievalStrategy = RetrievalStrategy.HYBRID) -> RetrieverPort:
        """按策略获取检索器"""
        return self._retrievers[strategy]


# 模块级单例
_container: Container | None = None


def _build_infra(settings: Settings):
    """实例化基础设施层：仓储、适配器、检索器"""
    from rag.infra.repositories.pg_project_repository import PgProjectRepository
    from rag.infra.repositories.pg_document_repository import PgDocumentRepository
    from rag.infra.repositories.pg_chunk_repository import PgChunkRepository
    from rag.infra.repositories.pg_embedding_repository import PgEmbeddingRepository
    from rag.infra.repositories.pg_embed_model_repository import PgEmbedModelRepository
    from rag.infra.repositories.pg_golden_repository import PgGoldenRepository
    from rag.infra.repositories.pg_golden_retrieval_repository import PgGoldenRetrievalRepository
    from rag.infra.repositories.pg_project_evaluation_repository import PgProjectEvaluationRepository
    from rag.infra.repositories.pg_profile_repository import PgProfileRepository
    from rag.infra.repositories.pg_qa_repository import PgQARepository
    from rag.infra.repositories.pg_user_repository import PgUserRepository
    from rag.infra.embedder.sentence_transformer import SentenceTransformerEmbedder
    from rag.infra.embedder.embedder_pool import EmbedderPool
    from rag.infra.retriever.pg_retriever import VectorRetriever
    from rag.infra.retriever.cosine_retriever import CosineRetriever
    from rag.infra.retriever.pg_bm25_retriever import PgBm25Retriever
    from rag.infra.retriever.hybrid_retriever import HybridRetriever
    from rag.infra.llm.dashscope_llm import DashScopeLLM
    from rag.infra.loader.file_document_loader import FileDocumentLoader
    from rag.infra.preprocessor.mkdocs_preprocessor import MkDocsPreprocessor
    from rag.infra.splitter.section_heading_splitter import SectionHeadingSplitter
    from rag.infra.storage.local_file_storage import LocalFileStorage

    # PG 仓储
    print("[INIT] 初始化 PG 仓储...", flush=True)
    pg_project_repo = PgProjectRepository()
    pg_document_repo = PgDocumentRepository()
    pg_chunk_repo = PgChunkRepository()
    pg_embedding_repo = PgEmbeddingRepository()
    pg_embed_model_repo = PgEmbedModelRepository()
    pg_golden_repo = PgGoldenRepository()
    pg_golden_retrieval_repo = PgGoldenRetrievalRepository()
    pg_project_evaluation_repo = PgProjectEvaluationRepository()
    pg_profile_repo = PgProfileRepository()
    pg_qa_repo = PgQARepository()
    pg_user_repo = PgUserRepository()

    # 基础设施适配器
    print("[INIT] 初始化基础设施适配器...", flush=True)
    embedder_pool = EmbedderPool(factory=SentenceTransformerEmbedder, max_size=3)
    model_scanner = ModelScanner(models_dir="models")
    file_storage = LocalFileStorage()
    loader = FileDocumentLoader()
    preprocessor = MkDocsPreprocessor()
    splitter = SectionHeadingSplitter(
        min_chars=settings.splitter_min_chars,
        max_chars=settings.splitter_max_chars,
    )
    llm = DashScopeLLM(
        api_key=settings.dashscope_api_key,
        base_url=settings.dashscope_base_url,
        model=settings.dashscope_model,
    )

    # 检索器
    cosine_retriever = CosineRetriever(
        embedder_pool=embedder_pool,
        embedding_repo=pg_embedding_repo,
        embed_model_repo=pg_embed_model_repo,
        project_repo=pg_project_repo,
    )
    vector_retriever = VectorRetriever(
        embedder_pool=embedder_pool,
        embedding_repo=pg_embedding_repo,
        embed_model_repo=pg_embed_model_repo,
        project_repo=pg_project_repo,
    )
    bm25_retriever = PgBm25Retriever(
        chunk_repo=pg_chunk_repo,
    )
    hybrid_retriever = HybridRetriever(
        vector_retriever=vector_retriever,
        bm25_retriever=bm25_retriever,
    )

    retrievers = {
        RetrievalStrategy.COSINE: cosine_retriever,
        RetrievalStrategy.VECTOR: vector_retriever,
        RetrievalStrategy.BM25: bm25_retriever,
        RetrievalStrategy.HYBRID: hybrid_retriever,
    }

    return {
        "pg_project_repo": pg_project_repo,
        "pg_document_repo": pg_document_repo,
        "pg_chunk_repo": pg_chunk_repo,
        "pg_embedding_repo": pg_embedding_repo,
        "pg_embed_model_repo": pg_embed_model_repo,
        "pg_golden_repo": pg_golden_repo,
        "pg_golden_retrieval_repo": pg_golden_retrieval_repo,
        "pg_project_evaluation_repo": pg_project_evaluation_repo,
        "pg_profile_repo": pg_profile_repo,
        "pg_qa_repo": pg_qa_repo,
        "pg_user_repo": pg_user_repo,
        "embedder_pool": embedder_pool,
        "model_scanner": model_scanner,
        "file_storage": file_storage,
        "loader": loader,
        "preprocessor": preprocessor,
        "splitter": splitter,
        "llm": llm,
        "retrievers": retrievers,
        "jwt_secret_key": settings.jwt_secret_key,
        "jwt_expire_hours": settings.jwt_expire_hours,
    }


def _build_usecases(infra: dict):
    """组装应用层用例"""
    scan_embed_models_usecase = ScanEmbedModelsUseCase(
        embed_model_repo=infra["pg_embed_model_repo"],
        model_scanner=infra["model_scanner"],
    )
    upload_usecase = UploadUseCase(
        document_repo=infra["pg_document_repo"],
        file_storage=infra["file_storage"],
    )
    process_document_usecase = ProcessDocumentUseCase(
        document_repo=infra["pg_document_repo"],
        chunk_repo=infra["pg_chunk_repo"],
        embedding_repo=infra["pg_embedding_repo"],
        project_repo=infra["pg_project_repo"],
        embed_model_repo=infra["pg_embed_model_repo"],
        loader=infra["loader"],
        splitter=infra["splitter"],
        embedder_pool=infra["embedder_pool"],
        preprocessor=infra["preprocessor"],
    )
    batch_process_usecase = BatchProcessDocumentUseCase(
        process_document_usecase=process_document_usecase,
    )
    golden_usecase = GoldenUseCase(
        golden_repo=infra["pg_golden_repo"],
        chunk_repo=infra["pg_chunk_repo"],
    )
    golden_retrieve_usecase = GoldenRetrieveUseCase(
        retrievers=infra["retrievers"],
        golden_repo=infra["pg_golden_repo"],
        golden_retrieval_repo=infra["pg_golden_retrieval_repo"],
        chunk_repo=infra["pg_chunk_repo"],
        project_repo=infra["pg_project_repo"],
        embed_model_repo=infra["pg_embed_model_repo"],
    )
    project_usecase = ProjectUseCase(
        project_repo=infra["pg_project_repo"],
        embed_model_repo=infra["pg_embed_model_repo"],
    )
    document_usecase = DocumentUseCase(
        document_repo=infra["pg_document_repo"],
        chunk_repo=infra["pg_chunk_repo"],
        embedding_repo=infra["pg_embedding_repo"],
        file_storage=infra["file_storage"],
        golden_repo=infra["pg_golden_repo"],
    )
    embed_model_usecase = EmbedModelUseCase(
        embed_model_repo=infra["pg_embed_model_repo"],
        project_repo=infra["pg_project_repo"],
        model_scanner=infra["model_scanner"],
    )
    profile_usecase = ProfileUseCase(
        profile_repo=infra["pg_profile_repo"],
        project_repo=infra["pg_project_repo"],
    )
    ask = AskUseCase(
        retriever=infra["retrievers"][RetrievalStrategy.HYBRID],
        chunk_repo=infra["pg_chunk_repo"],
        llm=infra["llm"],
    )
    qa = QAUseCase(
        retriever=infra["retrievers"][RetrievalStrategy.HYBRID],
        chunk_repo=infra["pg_chunk_repo"],
        llm=infra["llm"],
        qa_repo=infra["pg_qa_repo"],
    )
    from rag.application.usecases.retrieve import RetrieveUseCase
    retrieve = RetrieveUseCase(
        retriever=infra["retrievers"][RetrievalStrategy.HYBRID],
        chunk_repo=infra["pg_chunk_repo"],
    )
    evaluation_usecase = ProjectEvaluationUseCase(
        golden_repo=infra["pg_golden_repo"],
        golden_retrieval_repo=infra["pg_golden_retrieval_repo"],
        evaluation_repo=infra["pg_project_evaluation_repo"],
    )
    auth_usecase = AuthUseCase(
        user_repo=infra["pg_user_repo"],
        jwt_secret_key=infra.get("jwt_secret_key", "rag-internal-default-secret"),
        jwt_expire_hours=infra.get("jwt_expire_hours", 24),
    )

    return {
        "upload_usecase": upload_usecase,
        "process_document_usecase": process_document_usecase,
        "batch_process_usecase": batch_process_usecase,
        "golden_usecase": golden_usecase,
        "golden_retrieve_usecase": golden_retrieve_usecase,
        "evaluation_usecase": evaluation_usecase,
        "scan_embed_models_usecase": scan_embed_models_usecase,
        "project_usecase": project_usecase,
        "document_usecase": document_usecase,
        "embed_model_usecase": embed_model_usecase,
        "profile_usecase": profile_usecase,
        "auth_usecase": auth_usecase,
        "ask": ask,
        "qa": qa,
        "retrieve": retrieve,
    }


def build_container(settings: Settings | None = None) -> Container:
    global _container

    print("[LOAD] 加载基础设施模块...", flush=True)
    infra = _build_infra(settings)

    print("[LOAD] 组装用例...", flush=True)
    usecases = _build_usecases(infra)

    _container = Container(
        **usecases,
        settings=settings,
        model_scanner=infra["model_scanner"],
        _retrievers=infra["retrievers"],
    )

    return _container


def get_container() -> Container:
    """FastAPI 依赖注入用 — 获取或创建容器"""
    global _container
    if _container is None:
        _container = build_container()
    return _container
