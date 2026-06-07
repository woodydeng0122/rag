from __future__ import annotations

import json
import asyncio

from argparse import ArgumentParser


def register_args(p: ArgumentParser):
    p.add_argument("-f", "--file", type=str, required=True, help="黄金数据集 item JSON 文件路径")
    p.add_argument("-p", "--project-id", type=str, required=True, help="项目 ID")


def handle(args, container):
    """将黄金数据集 item JSON 写入黄金数据集表"""
    with open(args.file, "r", encoding="utf-8") as f:
        item = json.load(f)

    query = item.get("query", "").strip()
    if not query:
        raise ValueError("JSON 中 query 不能为空")

    ground_truth_chunks = item.get("ground_truth_chunks", [])
    reference_answer = item.get("reference_answer", "")
    metadata = item.get("metadata", {})

    record = asyncio.run(container.golden_dataset_usecase.create(
        project_id=args.project_id,
        query=query,
        ground_truth_chunks=ground_truth_chunks,
        reference_answer=reference_answer,
        metadata=metadata,
    ))

    print(f"黄金记录已写入: id={record.id}, query={record.query}")

