from __future__ import annotations

import json

from argparse import ArgumentParser


def register_args(p: ArgumentParser):
    p.add_argument("--format", choices=["text", "json"], default="text", help="输出格式，默认 text")


async def handle(args, settings):
    """列出所有项目"""
    from rag.infra.database.connection import db_connection, get_pool

    output_format = args.format

    async with db_connection(settings):
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT p.id, p.name, p.description, p.embed_dimension,
                          em.name AS embed_model_name,
                          p.created_at
                   FROM project p
                   LEFT JOIN embed_model em ON em.id = p.embed_model_id
                   ORDER BY p.created_at DESC"""
            )

        if not rows:
            if output_format == "json":
                print(json.dumps({"projects": []}, ensure_ascii=False))
            else:
                print("暂无项目。")
            return

        projects = [
            {
                "id": str(row["id"]),
                "name": row["name"],
                "description": row["description"] or "",
                "embed_dimension": row["embed_dimension"],
                "embed_model_name": row["embed_model_name"] or "",
                "created_at": str(row["created_at"]),
            }
            for row in rows
        ]

        if output_format == "json":
            print(json.dumps({"projects": projects}, ensure_ascii=False))
        else:
            print(f"共 {len(projects)} 个项目：")
            print("-" * 60)
            for p in projects:
                print(f"  {p['name']}")
                print(f"    ID: {p['id']}")
                print(f"    描述: {p['description'] or '(无)'}")
                print(f"    嵌入模型: {p['embed_model_name'] or '(未设置)'} (dim={p['embed_dimension']})")
                print()
