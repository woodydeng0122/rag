from __future__ import annotations

import json

from argparse import ArgumentParser


def register_args(p: ArgumentParser):
    p.add_argument("project", type=str, help="项目名称，如 FastApi")
    p.add_argument("--format", choices=["text", "json"], default="text", help="输出格式，默认 text")


async def handle(args, settings):
    """筛选指定项目中检索结果未命中的黄金记录条目，含分块内容"""
    from rag.infra.database.connection import db_connection, get_pool

    project_name = args.project
    output_format = args.format

    async with db_connection(settings):
        pool = get_pool()
        async with pool.acquire() as conn:
            # 查找项目
            project = await conn.fetchrow(
                "SELECT id, name FROM project WHERE name = $1", project_name
            )
            if project is None:
                print(f"未找到项目: {project_name}")
                return

            project_id = project["id"]

            # 查询有检索结果但未命中任何 ground_truth 的黄金记录
            rows = await conn.fetch(
                """SELECT g.id, g.query, g.ground_truth_chunks, g.reference_answer,
                          gr.id AS retrieval_id, gr.max_k, gr.latency_ms, gr.embed_model_name
                   FROM golden g
                   JOIN golden_retrieval gr ON gr.golden_id = g.id
                   WHERE g.project_id = $1
                     AND NOT EXISTS (
                       SELECT 1 FROM golden_retrieval_item ri
                       WHERE ri.retrieval_id = gr.id
                         AND ri.chunk_id = ANY(g.ground_truth_chunks)
                     )
                   ORDER BY g.created_at DESC""",
                project_id,
            )

        if not rows:
            if output_format == "json":
                print(json.dumps({"project": project_name, "miss_count": 0, "misses": []}, ensure_ascii=False))
            else:
                print(f"项目: {project['name']} ({project_id})")
                print("所有黄金记录均已命中，无未命中条目。")
            return

        misses = []
        for row in rows:
            gt_chunk_ids = list(row["ground_truth_chunks"]) if row["ground_truth_chunks"] else []

            # 查询期望分块内容
            gt_contents = {}
            retrieved_contents = {}
            async with pool.acquire() as conn:
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
                "query": row["query"],
                "ground_truth_chunk_ids": gt_chunk_ids,
                "ground_truth_chunks": gt_contents,
                "retrieved_chunks": retrieved_contents,
                "reference_answer": row["reference_answer"] or "",
                "max_k": row["max_k"],
                "latency_ms": row["latency_ms"],
                "embed_model_name": row["embed_model_name"],
            }
            misses.append(miss)

        if output_format == "json":
            print(json.dumps({"project": project_name, "miss_count": len(misses), "misses": misses}, ensure_ascii=False))
        else:
            print(f"项目: {project['name']} ({project_id})")
            print(f"未命中条目数: {len(misses)}")
            print("=" * 80)
            for i, m in enumerate(misses, 1):
                print(f"\n[{i}] ID: {m['id']}")
                print(f"    查询: {m['query']}")
                print(f"    期望分块 IDs: {m['ground_truth_chunk_ids']}")
                for cid, c in m["ground_truth_chunks"].items():
                    print(f"      [{cid}] {c['heading'] or '(无标题)'}")
                    print(f"        {c['content'][:200]}{'...' if len(c['content']) > 200 else ''}")
                print(f"    实际检索到 {len(m['retrieved_chunks'])} 个分块:")
                for rc in m["retrieved_chunks"]:
                    print(f"      [rank={rc['rank']}] score={rc['score']:.4f} {rc['heading'] or '(无标题)'}")
                    print(f"        {rc['content'][:200]}{'...' if len(rc['content']) > 200 else ''}")
                print(f"    参考答案: {m['reference_answer'] or '(无)'}")
                print(f"    检索参数: max_k={m['max_k']}, latency={m['latency_ms']}ms, model={m['embed_model_name']}")
