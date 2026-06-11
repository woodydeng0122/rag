from __future__ import annotations

from argparse import ArgumentParser

import jieba


def register_args(p: ArgumentParser):
    p.add_argument("--batch-size", type=int, default=500, help="每批处理的 chunk 数量")


async def handle(args, settings):
    """回填 chunk 表的 search_tokens 列 — 用 jieba 分词结果填充"""
    from rag.infra.database.connection import init_pool, close_pool, get_pool

    await init_pool(
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
    )

    try:
        pool = get_pool()
        batch_size = args.batch_size
        total_updated = 0
        offset = 0

        while True:
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    """SELECT id, content FROM chunk
                       WHERE search_tokens = '' OR search_tokens IS NULL
                       ORDER BY id
                       LIMIT $1""",
                    batch_size,
                )

            if not rows:
                break

            tokens_list = []
            for row in rows:
                tokens = " ".join(jieba.cut(row["content"]))
                tokens_list.append((tokens, row["id"]))

            async with pool.acquire() as conn:
                await conn.executemany(
                    "UPDATE chunk SET search_tokens = $1 WHERE id = $2",
                    tokens_list,
                )

            total_updated += len(rows)
            print(f"  已处理 {total_updated} 条...", flush=True)

        print(f"回填完成，共更新 {total_updated} 条 chunk 的 search_tokens。")
    finally:
        await close_pool()
