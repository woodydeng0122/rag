from __future__ import annotations

from argparse import ArgumentParser


def register_args(p: ArgumentParser):
    p.add_argument("-p", "--project-id", type=str, required=True, help="项目 ID")
    p.add_argument("-k", "--k", type=int, nargs="+", help="Recall@K 的 K 值")
    p.add_argument("-o", "--output", type=str, default="./eval_result.json", help="结果输出文件")


def handle(args, container):
    """评测命令"""
    import asyncio
    import json

    project_id = args.project_id

    records = asyncio.run(container.golden_usecase.list_by_project(project_id))
    golden_ids = [r.id for r in records if r.ground_truth_chunks]

    if not golden_ids:
        print("该项目没有黄金记录，无法评测。")
        return

    k_list = args.k or [10]
    result = asyncio.run(container.evaluate.execute_by_project(
        project_id=project_id,
        golden_ids=golden_ids,
        k_list=k_list,
    ))

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

