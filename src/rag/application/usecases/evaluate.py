import time as _time
from datetime import datetime

from rag.domain.entities.golden_record import GoldenRecord
from rag.domain.value_objects.evaluation_metrics import EvaluationMetrics
from rag.domain.value_objects.project_eval_summary import ProjectEvalSummary
from rag.domain.ports.retriever import RetrieverPort
from rag.domain.ports.golden_repository import GoldenRepositoryPort
from rag.domain.ports.project_repository import ProjectRepositoryPort
from rag.application.results.metrics import recall_at_k, calc_mrr
from rag.application.results.evaluate_result import EvaluateResult


class EvaluateUseCase:
    """评测用例 — 从 DB 加载黄金集 → 检索 → 计算指标 → 持久化结果"""

    def __init__(
        self,
        retriever: RetrieverPort,
        golden_repo: GoldenRepositoryPort,
        project_repo: ProjectRepositoryPort,
    ):
        self.retriever = retriever
        self.golden_repo = golden_repo
        self.project_repo = project_repo

    async def execute_by_project(
        self,
        project_id: str,
        golden_ids: list[str],
        k_list: list[int] | None = None,
    ) -> EvaluateResult:
        """按项目 ID 和黄金记录 ID 列表执行评测，持久化结果"""
        if not golden_ids:
            raise ValueError("golden_ids 不能为空")
        if k_list is None:
            k_list = [10]
        max_k = max(k_list)

        # 从 DB 加载黄金记录
        records: list[GoldenRecord] = []
        for gid in golden_ids:
            record = await self.golden_repo.get_by_id(gid)
            if record is not None:
                records.append(record)

        if not records:
            raise ValueError("未找到有效的黄金记录")

        # 计时：检索 + 指标计算
        start = _time.perf_counter()

        # 检索并更新每条记录
        for record in records:
            results = await self.retriever.retrieve(record.query, project_id=project_id, top_k=max_k)
            retrieved_ids = [r.chunk_id for r in results]

            # 计算命中信息
            gt_ids = set(record.ground_truth_chunks)
            hit_rank = None
            is_hit = False
            for i, chunk_id in enumerate(retrieved_ids, start=1):
                if chunk_id in gt_ids:
                    is_hit = True
                    hit_rank = i
                    break

            record.evaluation = EvaluationMetrics(
                retrieved_chunk_ids=retrieved_ids,
                is_hit=is_hit,
                hit_rank=hit_rank,
                evaluated_at=datetime.now(),
            )

            # 持久化单条评测结果
            await self.golden_repo.update(record)

        # 计算指标
        recall, failure_queries = recall_at_k(records, k_list)
        mrr = calc_mrr(records)

        total_elapsed = (_time.perf_counter() - start) * 1000

        # 更新项目评测汇总
        project = await self.project_repo.get_by_id(project_id)
        if project is not None:
            project.record_eval(ProjectEvalSummary(
                recall_at_10=recall.get("recall@10", {}).get("recall", 0) if "recall@10" in recall else None,
                mrr=mrr,
                answerable=len(records) - len(failure_queries),
                total=len(records),
                latency_avg_ms=round(total_elapsed / len(records), 2) if records else 0,
                evaluated_at=datetime.now(),
            ))
            await self.project_repo.update(project)

        return EvaluateResult(
            answerable_count=len(records) - len(failure_queries),
            recall=recall,
            mrr=mrr,
            failure=failure_queries,
            time=datetime.now().strftime("%Y%m%d %H:%M"),
            latency_total_ms=round(total_elapsed, 2),
            latency_avg_ms=round(total_elapsed / len(records), 2) if records else 0,
        )
