from __future__ import annotations

import json

from argparse import ArgumentParser


def register_args(p: ArgumentParser):
    p.add_argument("golden_id", type=str, help="黄金记录 ID")
    p.add_argument("--format", choices=["text", "json"], default="text", help="输出格式，默认 text")


async def handle(args, settings):
    """根据黄金记录 ID 查询检索未命中详情，含分块内容"""
    from rag.infra.database.connection import db_connection, get_pool

    golden_id = args.golden_id
    output_format = args.format

    async with db_connection(settings):
        pool = get_pool()
        async with pool.acquire() as conn:
            # 根据 golden_id 查询黄金记录及其检索结果
            row = await conn.fetchrow(
                """SELECT g.id, g.query, g.ground_truth_chunks, g.reference_answer,
                          gr.id AS retrieval_id, gr.max_k, gr.latency_ms, gr.embed_model_name,
                          p.name AS project_name
                   FROM golden g
                   JOIN golden_retrieval gr ON gr.golden_id = g.id
                   JOIN project p ON p.id = g.project_id
                   WHERE g.id = $1""",
                golden_id,
            )

            if row is None:
                if output_format == "json":
                    print(json.dumps({"error": f"未找到黄金记录: {golden_id}"}, ensure_ascii=False))
                else:
                    print(f"未找到黄金记录: {golden_id}")
                return

            gt_chunk_ids = list(row["ground_truth_chunks"]) if row["ground_truth_chunks"] else []

            # 查询期望分块内容
            gt_contents = {}
            if gt_chunk_ids:
                gt_rows = await conn.fetch(
                    "SELECT id, content, heading, source_file FROM chunk WHERE id = ANY($1)",
                    gt_chunk_ids,
                )
                gt_contents = {
                    str(r["id"]): {
                        "content": r["content"],
                        "heading": r["heading"],
                        "source_file": r["source_file"],
                    }
                    for r in gt_rows
                }

            # 查询实际检索到的分块
            ri_rows = await conn.fetch(
                """SELECT ri.chunk_id, ri.score, ri.rank, c.content, c.heading, c.source_file
                   FROM golden_retrieval_item ri
                   LEFT JOIN chunk c ON c.id = ri.chunk_id
                   WHERE ri.retrieval_id = $1
                   ORDER BY ri.rank""",
                row["retrieval_id"],
            )
            retrieved_contents = [
                {
                    "chunk_id": r["chunk_id"],
                    "score": float(r["score"]),
                    "rank": int(r["rank"]),
                    "content": r["content"] or "",
                    "heading": r["heading"] or "",
                    "source_file": r["source_file"] or "",
                }
                for r in ri_rows
            ]

        miss = {
            "id": str(row["id"]),
            "project": row["project_name"],
            "query": row["query"],
            "ground_truth_chunk_ids": gt_chunk_ids,
            "ground_truth_chunks": gt_contents,
            "retrieved_chunks": retrieved_contents,
            "reference_answer": row["reference_answer"] or "",
            "max_k": row["max_k"],
            "latency_ms": row["latency_ms"],
            "embed_model_name": row["embed_model_name"],
        }

        if output_format == "json":
            print(json.dumps(miss, ensure_ascii=False))
        else:
            print(f"项目: {row['project_name']}")
            print(f"黄金记录 ID: {row['id']}")
            print("=" * 80)
            print(f"查询: {miss['query']}")
            print(f"期望分块 IDs: {miss['ground_truth_chunk_ids']}")
            for cid, c in miss["ground_truth_chunks"].items():
                print(f"  [{cid}] {c['heading'] or '(无标题)'}")
                print(f"    {c['content'][:200]}{'...' if len(c['content']) > 200 else ''}")
            print(f"实际检索到 {len(miss['retrieved_chunks'])} 个分块:")
            for rc in miss["retrieved_chunks"]:
                print(f"  [rank={rc['rank']}] score={rc['score']:.4f} {rc['heading'] or '(无标题)'}")
                print(f"    {rc['content'][:200]}{'...' if len(rc['content']) > 200 else ''}")
            print(f"参考答案: {miss['reference_answer'] or '(无)'}")
            print(f"检索参数: max_k={miss['max_k']}, latency={miss['latency_ms']}ms, model={miss['embed_model_name']}")
