import time

from dataclasses import dataclass

from rag.domain.ports.retriever import RetrieverPort
from rag.domain.ports.golden_repository import GoldenRepositoryPort
from rag.domain.ports.golden_retrieval_repository import GoldenRetrievalRepositoryPort, RetrievalSummary
from rag.domain.ports.chunk_repository import ChunkRepositoryPort
from rag.domain.ports.project_repository import ProjectRepositoryPort
from rag.domain.ports.embed_model_repository import EmbedModelRepositoryPort
from rag.domain.entities.golden_retrieval import GoldenRetrieval
from rag.domain.entities.golden_retrieval_item import GoldenRetrievalItem


@dataclass
class RetrievalItemWithChunk:
    """检索结果项 — 含 chunk 内容和 GT 命中标记"""

    chunk_id: str
    score: float
    rank: int
    content: str
    heading: str
    source_file: str
    file_type: str
    is_ground_truth: bool


@dataclass
class GoldenRetrievalResult:
    """检索完整结果 — 含指标和明细"""

    id: str
    golden_id: str
    max_k: int
    latency_ms: int
    embed_model_name: str
    created_at: str
    items: list[RetrievalItemWithChunk]
    embed_latency_ms: int = 0
    search_latency_ms: int = 0
    load_embeddings_latency_ms: int = 0
    load_project_latency_ms: int = 0
    load_embed_model_latency_ms: int = 0
    get_embedder_latency_ms: int = 0
    build_matrix_latency_ms: int = 0


class GoldenRetrieveUseCase:
    """黄金记录检索用例 — 组合检索 + 持久化 + GT 命中计算"""

    def __init__(
        self,
        retriever: RetrieverPort,
        golden_repo: GoldenRepositoryPort,
        golden_retrieval_repo: GoldenRetrievalRepositoryPort,
        chunk_repo: ChunkRepositoryPort,
        project_repo: ProjectRepositoryPort,
        embed_model_repo: EmbedModelRepositoryPort,
    ):
        self._retriever = retriever
        self._golden_repo = golden_repo
        self._golden_retrieval_repo = golden_retrieval_repo
        self._chunk_repo = chunk_repo
        self._project_repo = project_repo
        self._embed_model_repo = embed_model_repo

    async def execute(self, record_id: str, max_k: int = 10) -> GoldenRetrievalResult:
        """触发检索 — 加载记录 → 检索 → 计时 → 持久化 → 返回结果"""
        # 加载黄金记录
        record = await self._golden_repo.get_by_id(record_id)
        if record is None:
            raise ValueError(f"黄金记录 {record_id} 不存在")

        # 获取项目关联的嵌入模型名称
        embed_model_name = ""
        project = await self._project_repo.get_by_id(record.project_id)
        if project and project.embed_model_id:
            embed_model = await self._embed_model_repo.get_by_id(project.embed_model_id)
            if embed_model and embed_model.is_online:
                embed_model_name = embed_model.name

        if not embed_model_name:
            raise ValueError("项目未配置在线嵌入模型，无法执行检索")

        # 执行检索并计时
        start = time.monotonic()
        output = await self._retriever.retrieve(
            query=record.query, project_id=record.project_id, top_k=max_k
        )
        latency_ms = int((time.monotonic() - start) * 1000)

        # 构建检索明细
        items = [
            GoldenRetrievalItem(
                retrieval_id="",  # save 时填充
                chunk_id=r.chunk_id,
                score=r.score,
                rank=i + 1,
            )
            for i, r in enumerate(output.results)
        ]

        # 持久化（覆盖模式）
        retrieval = GoldenRetrieval(
            golden_id=record_id,
            max_k=max_k,
            latency_ms=latency_ms,
            embed_model_name=embed_model_name,
            embed_latency_ms=output.embed_latency_ms,
            search_latency_ms=output.search_latency_ms,
            load_embeddings_latency_ms=output.load_embeddings_latency_ms,
            load_project_latency_ms=output.load_project_latency_ms,
            load_embed_model_latency_ms=output.load_embed_model_latency_ms,
            get_embedder_latency_ms=output.get_embedder_latency_ms,
            build_matrix_latency_ms=output.build_matrix_latency_ms,
        )
        saved = await self._golden_retrieval_repo.save(retrieval, items)

        # 返回完整结果（含 chunk 内容和 GT 命中）
        return await self._build_result(saved, items, record.project_id, record.ground_truth_chunks)

    async def get_retrieval(self, record_id: str) -> GoldenRetrievalResult:
        """获取检索结果 — 加载记录 → 查 retrieval → join chunk → GT 命中"""
        record = await self._golden_repo.get_by_id(record_id)
        if record is None:
            raise ValueError(f"黄金记录 {record_id} 不存在")

        result = await self._golden_retrieval_repo.get_by_golden_id(record_id)
        if result is None:
            raise ValueError(f"黄金记录 {record_id} 无检索结果")

        retrieval, items = result
        return await self._build_result(retrieval, items, record.project_id, record.ground_truth_chunks)

    async def has_retrieval_for_records(self, golden_ids: list[str]) -> set[str]:
        """批量查询哪些黄金记录有检索结果"""
        return await self._golden_retrieval_repo.exists_by_golden_ids(golden_ids)

    async def get_retrieval_summaries(self, golden_ids: list[str]) -> dict[str, RetrievalSummary]:
        """批量获取检索命中摘要"""
        return await self._golden_retrieval_repo.get_retrieval_summaries(golden_ids)

    async def _load_chunk_map(
        self,
        project_id: str,
        chunk_ids: list[str],
    ) -> dict:
        """批量加载 chunk 内容 — 按 ID 精准查询，附带 file_type"""
        if not chunk_ids:
            return {}
        results = await self._chunk_repo.get_by_ids_with_file_type(chunk_ids)
        return {c.id: (c, file_type) for c, file_type in results}

    async def _build_result(
        self,
        retrieval: GoldenRetrieval,
        items: list[GoldenRetrievalItem],
        project_id: str,
        ground_truth_chunks: list[str],
    ) -> GoldenRetrievalResult:
        """构建完整检索结果 — join chunk 内容 + GT 命中标记"""
        gt_set = set(ground_truth_chunks)

        # 批量加载 chunk 内容
        chunk_ids = [item.chunk_id for item in items]
        chunk_map = await self._load_chunk_map(project_id, chunk_ids)

        result_items = []
        for item in items:
            entry = chunk_map.get(item.chunk_id)
            chunk = entry[0] if entry else None
            file_type = entry[1] if entry else ""
            result_items.append(
                RetrievalItemWithChunk(
                    chunk_id=item.chunk_id,
                    score=item.score,
                    rank=item.rank,
                    content=chunk.content if chunk else "",
                    heading=chunk.heading if chunk else "",
                    source_file=chunk.source_file if chunk else "",
                    file_type=file_type,
                    is_ground_truth=item.chunk_id in gt_set,
                )
            )

        return GoldenRetrievalResult(
            id=retrieval.id,
            golden_id=retrieval.golden_id,
            max_k=retrieval.max_k,
            latency_ms=retrieval.latency_ms,
            embed_model_name=retrieval.embed_model_name,
            created_at=retrieval.created_at.isoformat() if retrieval.created_at else "",
            items=result_items,
            embed_latency_ms=retrieval.embed_latency_ms,
            search_latency_ms=retrieval.search_latency_ms,
            load_embeddings_latency_ms=retrieval.load_embeddings_latency_ms,
            load_project_latency_ms=retrieval.load_project_latency_ms,
            load_embed_model_latency_ms=retrieval.load_embed_model_latency_ms,
            get_embedder_latency_ms=retrieval.get_embedder_latency_ms,
            build_matrix_latency_ms=retrieval.build_matrix_latency_ms,
        )
