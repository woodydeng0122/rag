import time

from dataclasses import dataclass, field

from rag.domain.ports.reranker import RerankerPort
from rag.domain.ports.golden_repository import GoldenRepositoryPort
from rag.domain.ports.golden_retrieval_repository import GoldenRetrievalRepositoryPort
from rag.domain.ports.golden_rerank_repository import GoldenRerankRepositoryPort, RerankSummary
from rag.domain.ports.chunk_repository import ChunkRepositoryPort
from rag.domain.entities.golden_rerank import GoldenRerank
from rag.domain.entities.golden_rerank_item import GoldenRerankItem


@dataclass
class RerankItemWithChunk:
    """重排结果项 — 含 chunk 内容和 GT 命中标记"""

    chunk_id: str
    original_rank: int
    rerank_score: float
    rerank_rank: int
    content: str
    heading: str
    source_file: str
    file_type: str
    is_ground_truth: bool


@dataclass
class GoldenRerankResult:
    """重排完整结果 — 含指标和明细"""

    id: str
    golden_id: str
    top_k: int
    latency_ms: int
    model_name: str
    created_at: str
    items: list[RerankItemWithChunk] = field(default_factory=list)


class GoldenRerankUseCase:
    """黄金记录重排用例 — 从粗排结果中取前 N 个候选，经 cross-encoder 重排后持久化"""

    def __init__(
        self,
        reranker: RerankerPort,
        golden_repo: GoldenRepositoryPort,
        golden_retrieval_repo: GoldenRetrievalRepositoryPort,
        golden_rerank_repo: GoldenRerankRepositoryPort,
        chunk_repo: ChunkRepositoryPort,
    ):
        self._reranker = reranker
        self._golden_repo = golden_repo
        self._golden_retrieval_repo = golden_retrieval_repo
        self._golden_rerank_repo = golden_rerank_repo
        self._chunk_repo = chunk_repo

    async def execute(self, record_id: str, top_k: int = 10) -> GoldenRerankResult:
        """触发重排 — 读取粗排 → 取前 top_k 候选 → reranker 重排 → 持久化 → 返回"""
        # 加载黄金记录
        record = await self._golden_repo.get_by_id(record_id)
        if record is None:
            raise ValueError(f"黄金记录 {record_id} 不存在")

        # 加载粗排结果
        retrieval_result = await self._golden_retrieval_repo.get_by_golden_id(record_id)
        if retrieval_result is None:
            raise ValueError(f"黄金记录 {record_id} 无粗排结果，请先执行检索")

        retrieval, retrieval_items = retrieval_result

        # 校验 top_k ≤ 粗排 max_k
        if top_k > retrieval.max_k:
            raise ValueError(f"top_k ({top_k}) 不能超过粗排 max_k ({retrieval.max_k})")

        # 取粗排前 top_k 个候选（按 rank 升序）
        sorted_items = sorted(retrieval_items, key=lambda x: x.rank)
        candidates = sorted_items[:top_k]

        # 加载候选 chunk 内容
        chunk_ids = [item.chunk_id for item in candidates]
        chunk_map = await self._load_chunk_map(record.project_id, chunk_ids)

        # 构建文档列表（用于 reranker 输入）
        documents = []
        for item in candidates:
            entry = chunk_map.get(item.chunk_id)
            documents.append(entry[0].content if entry else "")

        # 执行重排
        start = time.monotonic()
        rerank_results = await self._reranker.rerank(
            query=record.query, documents=documents, top_k=top_k
        )
        latency_ms = int((time.monotonic() - start) * 1000)

        # 构建重排明细
        rerank_items = []
        for rank_offset, result in enumerate(rerank_results):
            original_item = candidates[result.index]
            rerank_items.append(
                GoldenRerankItem(
                    rerank_id="",  # save 时填充
                    chunk_id=original_item.chunk_id,
                    original_rank=original_item.rank,
                    rerank_score=result.score,
                    rerank_rank=rank_offset + 1,
                )
            )

        # 持久化（覆盖模式）
        rerank = GoldenRerank(
            golden_id=record_id,
            top_k=top_k,
            latency_ms=latency_ms,
            model_name="BAAI/bge-reranker-base",
        )
        saved = await self._golden_rerank_repo.save(rerank, rerank_items)

        # 返回完整结果（含 chunk 内容和 GT 命中）
        return await self._build_result(saved, rerank_items, record.project_id, record.ground_truth_chunks)

    async def get_rerank(self, record_id: str) -> GoldenRerankResult:
        """获取重排结果"""
        record = await self._golden_repo.get_by_id(record_id)
        if record is None:
            raise ValueError(f"黄金记录 {record_id} 不存在")

        result = await self._golden_rerank_repo.get_by_golden_id(record_id)
        if result is None:
            raise ValueError(f"黄金记录 {record_id} 无重排结果")

        rerank, items = result
        return await self._build_result(rerank, items, record.project_id, record.ground_truth_chunks)

    async def has_rerank_for_records(self, golden_ids: list[str]) -> set[str]:
        """批量查询哪些黄金记录有重排结果"""
        return await self._golden_rerank_repo.exists_by_golden_ids(golden_ids)

    async def get_rerank_summaries(self, golden_ids: list[str]) -> dict[str, RerankSummary]:
        """批量获取重排命中摘要"""
        return await self._golden_rerank_repo.get_rerank_summaries(golden_ids)

    async def _load_chunk_map(self, project_id: str, chunk_ids: list[str]) -> dict:
        """批量加载 chunk 内容"""
        if not chunk_ids:
            return {}
        results = await self._chunk_repo.get_by_ids_with_file_type(chunk_ids)
        return {c.id: (c, file_type) for c, file_type in results}

    async def _build_result(
        self,
        rerank: GoldenRerank,
        items: list[GoldenRerankItem],
        project_id: str,
        ground_truth_chunks: list[str],
    ) -> GoldenRerankResult:
        """构建完整重排结果 — join chunk 内容 + GT 命中标记"""
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
                RerankItemWithChunk(
                    chunk_id=item.chunk_id,
                    original_rank=item.original_rank,
                    rerank_score=item.rerank_score,
                    rerank_rank=item.rerank_rank,
                    content=chunk.content if chunk else "",
                    heading=chunk.heading if chunk else "",
                    source_file=chunk.source_file if chunk else "",
                    file_type=file_type,
                    is_ground_truth=item.chunk_id in gt_set,
                )
            )

        return GoldenRerankResult(
            id=rerank.id,
            golden_id=rerank.golden_id,
            top_k=rerank.top_k,
            latency_ms=rerank.latency_ms,
            model_name=rerank.model_name,
            created_at=rerank.created_at.isoformat() if rerank.created_at else "",
            items=result_items,
        )
