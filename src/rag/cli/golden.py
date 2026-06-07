from __future__ import annotations

import json
import asyncio


def cmd_add_golden(args, golden_dataset_usecase, project_id: str):
    """将黄金数据集 item JSON 写入黄金数据集表"""
    with open(args.file, "r", encoding="utf-8") as f:
        item = json.load(f)

    query = item.get("query", "").strip()
    if not query:
        raise ValueError("JSON 中 query 不能为空")

    ground_truth_chunks = item.get("ground_truth_chunks", [])
    reference_answer = item.get("reference_answer", "")
    metadata = item.get("metadata", {})

    record = asyncio.run(golden_dataset_usecase.create(
        project_id=project_id,
        query=query,
        ground_truth_chunks=ground_truth_chunks,
        reference_answer=reference_answer,
        metadata=metadata,
    ))

    print(f"黄金记录已写入: id={record.id}, query={record.query}")
