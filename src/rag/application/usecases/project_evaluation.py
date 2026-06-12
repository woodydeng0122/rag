import math

from rag.domain.entities.golden_retrieval import GoldenRetrieval
from rag.domain.entities.golden_retrieval_item import GoldenRetrievalItem
from rag.domain.entities.golden_rerank import GoldenRerank
from rag.domain.entities.golden_rerank_item import GoldenRerankItem
from rag.domain.entities.project_evaluation import ProjectEvaluation, EvaluationCategory
from rag.domain.ports.golden_repository import GoldenRepositoryPort
from rag.domain.ports.golden_retrieval_repository import GoldenRetrievalRepositoryPort
from rag.domain.ports.golden_rerank_repository import GoldenRerankRepositoryPort
from rag.domain.ports.project_evaluation_repository import ProjectEvaluationRepositoryPort
from rag.domain.ports.project_repository import ProjectRepositoryPort
from rag.domain.value_objects.retrieval_strategy import RetrievalStrategy


def _compute_ndcg(ranks: list[int], gt_count: int, top_k: int) -> float:
    """计算 NDCG@{top_k}

    ranks: GT chunk 在返回列表中的排名列表（1-based）
    gt_count: GT chunk 总数
    top_k: 截断位置
    """
    if not ranks or gt_count == 0:
        return 0.0

    # DCG: 只考虑 rank ≤ top_k 的 GT
    dcg = 0.0
    for rank in ranks:
        if rank <= top_k:
            dcg += 1.0 / math.log2(rank + 1)

    # IDCG: 理想情况下所有 GT 都排在最前面
    ideal_count = min(gt_count, top_k)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_count))

    return dcg / idcg if idcg > 0 else 0.0


class ProjectEvaluationUseCase:
    """项目评估统计用例 — 基于已有检索/重排结果计算综合指标"""

    def __init__(
        self,
        golden_repo: GoldenRepositoryPort,
        golden_retrieval_repo: GoldenRetrievalRepositoryPort,
        evaluation_repo: ProjectEvaluationRepositoryPort,
        golden_rerank_repo: GoldenRerankRepositoryPort | None = None,
        project_repo: ProjectRepositoryPort | None = None,
    ):
        self._golden_repo = golden_repo
        self._golden_retrieval_repo = golden_retrieval_repo
        self._evaluation_repo = evaluation_repo
        self._golden_rerank_repo = golden_rerank_repo
        self._project_repo = project_repo

    async def execute(
        self,
        project_id: str,
        top_k: int = 10,
        strategy: RetrievalStrategy = RetrievalStrategy.HYBRID,
        category: EvaluationCategory = EvaluationCategory.RECALL,
        remark: str = "",
    ) -> ProjectEvaluation:
        """触发评估 — 根据 category 选择粗排/重排评估"""
        if category == EvaluationCategory.RERANK:
            return await self._execute_rerank_eval(project_id, top_k, remark)
        return await self._execute_recall_eval(project_id, top_k, strategy, remark)

    async def _execute_recall_eval(
        self, project_id: str, top_k: int, strategy: RetrievalStrategy, remark: str
    ) -> ProjectEvaluation:
        """粗排评估 — 基于已有检索结果计算指标"""
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
        ndcg_sum = 0.0
        hit_count_total = 0
        gt_total = 0
        full_hit_count = 0
        zero_hit_count = 0
        latency_sum = 0.0
        embed_latency_sum = 0.0
        search_latency_sum = 0.0
        embed_model_name = ""

        for retrieval, items in retrieval_data:
            # 按 top_k 截断
            filtered_items = [item for item in items if item.rank <= top_k]

            # 获取该记录的 GT
            gt_chunks = gt_map.get(retrieval.golden_id, set())
            if not gt_chunks:
                # GT 为空，跳过 recall/MRR/NDCG 计算，但仍计入延迟
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

            # NDCG
            ndcg_sum += _compute_ndcg(gt_ranks, len(gt_chunks), top_k)

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
        ndcg = ndcg_sum / records_with_gt if records_with_gt > 0 else 0.0
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
            ndcg=ndcg,
            hit_rate=hit_rate,
            full_hit_count=full_hit_count,
            zero_hit_count=zero_hit_count,
            avg_latency_ms=avg_latency_ms,
            avg_embed_latency_ms=avg_embed_latency_ms,
            avg_search_latency_ms=avg_search_latency_ms,
            category=EvaluationCategory.RECALL,
            strategy=strategy,
            embed_model_name=embed_model_name,
            remark=remark,
        )

        return await self._evaluation_repo.save(evaluation)

    async def _execute_rerank_eval(
        self, project_id: str, top_k: int, remark: str
    ) -> ProjectEvaluation:
        """重排评估 — 基于已有重排结果计算指标"""
        if self._golden_rerank_repo is None:
            raise ValueError("重排仓储未初始化")

        # 校验项目是否配置了重排模型
        if self._project_repo is not None:
            project = await self._project_repo.get_by_id(project_id)
            if project is None or not project.rerank_model_id:
                raise ValueError("项目未配置重排模型")

        # 加载项目下所有黄金记录
        golden_records = await self._golden_repo.list_by_project(project_id)
        golden_total = len(golden_records)

        if not golden_records:
            raise ValueError("项目无黄金记录")

        # 构建 golden_id → ground_truth_chunks 映射
        gt_map: dict[str, set[str]] = {
            r.id: set(r.ground_truth_chunks) for r in golden_records
        }

        # 加载项目下所有重排结果
        rerank_data: list[tuple[GoldenRerank, list[GoldenRerankItem]]] = []
        for record in golden_records:
            result = await self._golden_rerank_repo.get_by_golden_id(record.id)
            if result is not None:
                rerank_data.append(result)

        if not rerank_data:
            raise ValueError("项目无重排结果，请先执行重排")

        golden_retrieved = len(rerank_data)

        # 加载项目下所有检索结果，用于获取 embed/search 延迟
        retrieval_data = await self._golden_retrieval_repo.list_by_project_with_items(project_id)
        retrieval_map: dict[str, GoldenRetrieval] = {
            r.golden_id: r for r, _ in retrieval_data
        }

        # 按 top_k 截断后计算指标
        recall_sum = 0.0
        mrr_sum = 0.0
        ndcg_sum = 0.0
        hit_count_total = 0
        gt_total = 0
        full_hit_count = 0
        zero_hit_count = 0
        latency_sum = 0.0
        embed_latency_sum = 0.0
        search_latency_sum = 0.0
        model_name = ""

        for rerank, items in rerank_data:
            # 按 top_k 截断（按 rerank_rank）
            filtered_items = [item for item in items if item.rerank_rank <= top_k]

            # 获取该记录的 GT
            gt_chunks = gt_map.get(rerank.golden_id, set())
            if not gt_chunks:
                latency_sum += rerank.latency_ms
                # 累加对应粗排的 embed/search 延迟
                retrieval = retrieval_map.get(rerank.golden_id)
                if retrieval:
                    embed_latency_sum += retrieval.embed_latency_ms
                    search_latency_sum += retrieval.search_latency_ms
                if rerank.model_name:
                    model_name = rerank.model_name
                continue

            # recall@{top_k}
            reranked_chunks = {item.chunk_id for item in filtered_items}
            hit = reranked_chunks & gt_chunks
            recall_i = len(hit) / len(gt_chunks)
            recall_sum += recall_i

            # MRR
            gt_ranks = sorted(
                [item.rerank_rank for item in filtered_items if item.chunk_id in gt_chunks]
            )
            if gt_ranks:
                mrr_sum += 1.0 / gt_ranks[0]

            # NDCG
            ndcg_sum += _compute_ndcg(gt_ranks, len(gt_chunks), top_k)

            # hit_rate 相关
            hit_count_total += len(hit)
            gt_total += len(gt_chunks)

            # full_hit / zero_hit
            if len(hit) == len(gt_chunks):
                full_hit_count += 1
            if len(hit) == 0:
                zero_hit_count += 1

            # 延迟
            latency_sum += rerank.latency_ms
            # 累加对应粗排的 embed/search 延迟
            retrieval = retrieval_map.get(rerank.golden_id)
            if retrieval:
                embed_latency_sum += retrieval.embed_latency_ms
                search_latency_sum += retrieval.search_latency_ms
            if rerank.model_name:
                model_name = rerank.model_name

        # 计算平均值
        records_with_gt = golden_retrieved
        recall_at_k = recall_sum / records_with_gt if records_with_gt > 0 else 0.0
        mrr = mrr_sum / records_with_gt if records_with_gt > 0 else 0.0
        ndcg = ndcg_sum / records_with_gt if records_with_gt > 0 else 0.0
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
            ndcg=ndcg,
            hit_rate=hit_rate,
            full_hit_count=full_hit_count,
            zero_hit_count=zero_hit_count,
            avg_latency_ms=avg_latency_ms,
            avg_embed_latency_ms=avg_embed_latency_ms,
            avg_search_latency_ms=avg_search_latency_ms,
            category=EvaluationCategory.RERANK,
            strategy=RetrievalStrategy.HYBRID,
            embed_model_name=model_name,
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

    async def update_evaluation(self, evaluation_id: str, strategy: RetrievalStrategy | None = None, remark: str | None = None) -> bool:
        """更新评估记录策略和/或备注"""
        updates: dict = {}
        if strategy is not None:
            updates["strategy"] = strategy
        if remark is not None:
            updates["remark"] = remark
        if not updates:
            return True
        updated = await self._evaluation_repo.update(evaluation_id, **updates)
        if not updated:
            raise ValueError("评估记录不存在")
        return True
