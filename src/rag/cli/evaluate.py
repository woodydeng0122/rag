from __future__ import annotations


def cmd_eval(args, evaluate: EvaluateUseCase, project_id: str):
    """评测命令"""
    import asyncio

    # 从 DB 获取项目的黄金记录 ID
    from rag.bootstrap.container import get_container
    container = get_container()
    records = asyncio.run(container.golden_dataset_usecase.list_by_project(project_id))
    golden_ids = [r.id for r in records if r.ground_truth_chunks]

    if not golden_ids:
        print("该项目没有黄金记录，无法评测。")
        return

    k_list = args.k or [10]
    result = asyncio.run(evaluate.execute_by_project(
        project_id=project_id,
        golden_ids=golden_ids,
        k_list=k_list,
    ))

    import json
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump({
            "time": result.time,
            "answerable_count": result.answerable_count,
            "recall": result.recall,
            "mrr": result.mrr,
            "latency_total_ms": result.latency_total_ms,
            "latency_avg_ms": result.latency_avg_ms,
            "failure": result.failure,
        }, f, ensure_ascii=False, indent=2)
    print(f"评测结果已保存到 {args.output}")
