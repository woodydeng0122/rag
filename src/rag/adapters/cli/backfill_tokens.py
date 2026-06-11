from __future__ import annotations

from argparse import ArgumentParser

import jieba
import re


def _extract_english_words(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z]{2,}", text)
    seen = set()
    result = []
    for w in words:
        lw = w.lower()
        if lw not in seen:
            seen.add(lw)
            result.append(lw)
    return result


def _tokenize(text: str) -> str:
    english_words = _extract_english_words(text)
    chinese_tokens = [t for t in jieba.cut(text) if t.strip() and not re.match(r"^[A-Za-z]{2,}$", t)]
    all_tokens = english_words + chinese_tokens
    return " ".join(all_tokens)


def register_args(p: ArgumentParser):
    p.add_argument("--batch-size", type=int, default=500, help="每批处理的 chunk 数量")
    p.add_argument("--force", action="store_true", help="强制重写所有 chunk（即使已有 search_tokens）")


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

        # 强制重写所有 chunk，不依赖 search_tokens 是否为空
        force = getattr(args, "force", False)
        where_clause = "" if force else "WHERE search_tokens = '' OR search_tokens IS NULL"

        while True:
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    f"""SELECT id, content FROM chunk {where_clause}
                       ORDER BY id
                       LIMIT $1 OFFSET $2""",
                    batch_size,
                    offset,
                )

            if not rows:
                break

            tokens_list = []
            for row in rows:
                tokens = _tokenize(row["content"])
                tokens_list.append((tokens, row["id"]))

            async with pool.acquire() as conn:
                await conn.executemany(
                    "UPDATE chunk SET search_tokens = $1 WHERE id = $2",
                    tokens_list,
                )

            total_updated += len(rows)
            offset += batch_size
            print(f"  已处理 {total_updated} 条...", flush=True)

        print(f"回填完成，共更新 {total_updated} 条 chunk 的 search_tokens。")
    finally:
        await close_pool()
