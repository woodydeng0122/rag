from rag.domain.entities.golden_record import GoldenRecord


def recall_at_k(
    records: list[GoldenRecord], k_list: list[int]
) -> tuple[dict, list[str]]:
    """计算 Recall@K — 在 top-K 检索结果中命中的比例

    返回 (recall_dict, failure_queries)
    """
    total = len(records)
    hits = {k: 0 for k in k_list}
    failure_queries = []

    for record in records:
        gt_ids = set(record.ground_truth_chunks)
        retrieved = record.evaluation.retrieved_chunk_ids if record.evaluation else []
        hit_any = False
        for k in k_list:
            retrieved_set = set(retrieved[:k])
            if gt_ids & retrieved_set:
                hits[k] += 1
                hit_any = True
        if not hit_any:
            failure_queries.append(record.query)

    recall = {
        f"recall@{k}": {"hits": hits[k], "recall": round(hits[k] / total, 2)}
        for k in k_list
    }
    return recall, failure_queries


def calc_mrr(records: list[GoldenRecord]) -> float:
    """计算 MRR（Mean Reciprocal Rank）— 第一个正确结果的排名倒数的均值"""
    total = len(records)
    reciprocal_ranks = []

    for record in records:
        gt_ids = set(record.ground_truth_chunks)
        retrieved = record.evaluation.retrieved_chunk_ids if record.evaluation else []
        rank = 0
        for i, chunk_id in enumerate(retrieved, start=1):
            if chunk_id in gt_ids:
                rank = i
                break
        reciprocal_ranks.append(1 / rank if rank > 0 else 0.0)

    return round(sum(reciprocal_ranks) / total, 4)
