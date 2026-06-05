import time as _time
from datetime import datetime

from rag.domain.entities.golden_record import GoldenRecord
from rag.domain.ports.retriever import RetrieverPort
from rag.domain.services.metrics import recall_at_k, calc_mrr
from rag.application.results.evaluate_result import EvaluateResult


class EvaluateUseCase:
    """评测用例 — 遍历黄金集 → 检索 → 计算 Recall/MRR

    只依赖端口接口和领域服务，不知道具体实现。
    """

    def __init__(
        self,
        retriever: RetrieverPort,
        embedding_file: str = "",
        golden_file: str = "",
        embedder_model: str = "",
    ):
        self.retriever = retriever
        self._embedding_file = embedding_file
        self._golden_file = golden_file
        self._embedder_model = embedder_model

    def execute(
        self,
        records: list[dict],
        k_list: list[int] | None = None,
    ) -> EvaluateResult:
        if k_list is None:
            k_list = [10]
        max_k = max(k_list)

        # 构建 GoldenRecord
        golden_records = [
            GoldenRecord(
                query=r["query"],
                ground_truth_chunks=r.get("ground_truth_chunks", []),
                reference_answer=r.get("reference_answer", ""),
            )
            for r in records if r.get("ground_truth_chunks")
        ]

        # 计时：检索 + 指标计算
        start = _time.perf_counter()

        # 检索
        for record in golden_records:
            results = self.retriever.retrieve(record.query, top_k=max_k)
            record.set_retrieved([r.chunk_id for r in results])

        # 计算指标（委托领域服务）
        recall, failure_queries = recall_at_k(golden_records, k_list)
        mrr = calc_mrr(golden_records)

        total_elapsed = (_time.perf_counter() - start) * 1000

        return EvaluateResult(
            answerable_count=len(golden_records),
            recall=recall,
            mrr=mrr,
            failure=failure_queries,
            embedding_file=self._embedding_file,
            golden_file=self._golden_file,
            embedder_model=self._embedder_model,
            time=datetime.now().strftime("%Y%m%d %H:%M"),
            latency_total_ms=round(total_elapsed, 2),
            latency_avg_ms=round(total_elapsed / len(golden_records), 2) if golden_records else 0,
        )
