from rag.domain.entities.golden_record import GoldenRecord
from rag.domain.entities.golden_retrieval import GoldenRetrieval
from rag.domain.entities.golden_retrieval_item import GoldenRetrievalItem
from rag.domain.entities.project_evaluation import ProjectEvaluation
from rag.domain.ports.golden_repository import GoldenRepositoryPort
from rag.domain.ports.golden_retrieval_repository import GoldenRetrievalRepositoryPort
from rag.domain.ports.project_evaluation_repository import ProjectEvaluationRepositoryPort
from rag.domain.value_objects.retrieval_strategy import RetrievalStrategy


class ProjectEvaluationUseCase:
    """项目评估统计用例 — 基于已有检索结果计算综合指标"""

    def __init__(
        self,
        golden_repo: GoldenRepositoryPort,
        golden_retrieval_repo: GoldenRetrievalRepositoryPort,
        evaluation_repo: ProjectEvaluationRepositoryPort,
    ):
        self._golden_repo = golden_repo
        self._golden_retrieval_repo = golden_retrieval_repo
        self._evaluation_repo = evaluation_repo

    async def execute(self, project_id: str, top_k: int = 10, remark: str = "") -> ProjectEvaluation:
        """触发评估 — 加载检索结果 → 按 top_k 截断 → 计算指标 → 持久化"""
        # 加载项目下所有黄金记录
        golden_records = await self._golden_repo.list_by_project(project_id)
        golden_total = len(golden_records)

        if not golden_records:
            raise ValueError("项目无黄金记录")

        # 构建 golden_id → ground_truth_chunks 映射
        gt_map: dict[str, set[str]] = {
            r.id: set(r.ground_truth_chunks) for r in golden_records
        }

        # 加载项目下所有检索结果及明细
        retrieval_data = await self._golden_retrieval_repo.list_by_project_with_items(project_id)
        if not retrieval_data:
            raise ValueError("项目无检索结果，请先执行检索")

        golden_retrieved = len(retrieval_data)

        # 按 top_k 截断后计算指标
        recall_sum = 0.0
        mrr_sum = 0.0
        hit_count_total = 0
        gt_total = 0
        full_hit_count = 0
        zero_hit_count = 0
        latency_sum = 0.0
        embed_latency_sum = 0.0
        search_latency_sum = 0.0
        embed_model_name = ""
        strategy = RetrievalStrategy.HYBRID

        for retrieval, items in retrieval_data:
            # 取第一个检索结果的 strategy
            if strategy == RetrievalStrategy.HYBRID and retrieval.strategy:
                strategy = retrieval.strategy
            # 按 top_k 截断
            filtered_items = [item for item in items if item.rank <= top_k]

            # 获取该记录的 GT
            gt_chunks = gt_map.get(retrieval.golden_id, set())
            if not gt_chunks:
                # GT 为空，跳过 recall/MRR 计算，但仍计入延迟
                latency_sum += retrieval.latency_ms
                embed_latency_sum += retrieval.embed_latency_ms
                search_latency_sum += retrieval.search_latency_ms
                if retrieval.embed_model_name:
                    embed_model_name = retrieval.embed_model_name
                continue

            # recall@{top_k}
            retrieved_chunks = {item.chunk_id for item in filtered_items}
            hit = retrieved_chunks & gt_chunks
            recall_i = len(hit) / len(gt_chunks)
            recall_sum += recall_i

            # MRR
            gt_ranks = sorted(
                [item.rank for item in filtered_items if item.chunk_id in gt_chunks]
            )
            if gt_ranks:
                mrr_sum += 1.0 / gt_ranks[0]
            # else: rr=0, 不加

            # hit_rate 相关
            hit_count_total += len(hit)
            gt_total += len(gt_chunks)

            # full_hit / zero_hit
            if len(hit) == len(gt_chunks):
                full_hit_count += 1
            if len(hit) == 0:
                zero_hit_count += 1

            # 延迟
            latency_sum += retrieval.latency_ms
            embed_latency_sum += retrieval.embed_latency_ms
            search_latency_sum += retrieval.search_latency_ms
            if retrieval.embed_model_name:
                embed_model_name = retrieval.embed_model_name

        # 计算平均值（基于有 GT 的记录数）
        records_with_gt = golden_retrieved  # 简化：所有检索记录参与平均
        recall_at_k = recall_sum / records_with_gt if records_with_gt > 0 else 0.0
        mrr = mrr_sum / records_with_gt if records_with_gt > 0 else 0.0
        hit_rate = hit_count_total / gt_total if gt_total > 0 else 0.0
        avg_latency_ms = latency_sum / golden_retrieved if golden_retrieved > 0 else 0.0
        avg_embed_latency_ms = embed_latency_sum / golden_retrieved if golden_retrieved > 0 else 0.0
        avg_search_latency_ms = search_latency_sum / golden_retrieved if golden_retrieved > 0 else 0.0

        evaluation = ProjectEvaluation(
            project_id=project_id,
            top_k=top_k,
            golden_total=golden_total,
            golden_retrieved=golden_retrieved,
            recall_at_k=recall_at_k,
            mrr=mrr,
            hit_rate=hit_rate,
            full_hit_count=full_hit_count,
            zero_hit_count=zero_hit_count,
            avg_latency_ms=avg_latency_ms,
            avg_embed_latency_ms=avg_embed_latency_ms,
            avg_search_latency_ms=avg_search_latency_ms,
            strategy=strategy,
            embed_model_name=embed_model_name,
            remark=remark,
        )

        return await self._evaluation_repo.save(evaluation)

    async def list_evaluations(self, project_id: str) -> list[ProjectEvaluation]:
        """查询评估历史"""
        return await self._evaluation_repo.list_by_project(project_id)

    async def delete_evaluation(self, evaluation_id: str) -> bool:
        """删除评估记录"""
        deleted = await self._evaluation_repo.delete(evaluation_id)
        if not deleted:
            raise ValueError("评估记录不存在")
        return True

    async def update_remark(self, evaluation_id: str, remark: str) -> bool:
        """更新评估记录备注"""
        updated = await self._evaluation_repo.update_remark(evaluation_id, remark)
        if not updated:
            raise ValueError("评估记录不存在")
        return True
