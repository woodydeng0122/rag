"""诊断 BM25 召回率 — 验证英文词提取后的效果"""
import asyncio
import asyncpg
import os
import urllib.parse

from dotenv import load_dotenv
load_dotenv()

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


def _build_or_tsquery(text: str) -> str:
    english_words = _extract_english_words(text)
    chinese_tokens = jieba.cut(text)
    chinese_terms = [
        t.strip() for t in chinese_tokens
        if t.strip() and len(t.strip()) > 1 and not re.match(r"^[A-Za-z]{2,}$", t)
    ]
    all_terms = english_words + chinese_terms
    if not all_terms:
        all_terms = [t.strip() for t in jieba.cut(text) if t.strip()]
    return " | ".join(all_terms)


async def check():
    url = os.getenv("DATABASE_URL", "")
    p = urllib.parse.urlparse(url)
    conn = await asyncpg.connect(
        host=p.hostname, port=p.port,
        database=p.path.lstrip("/"),
        user=p.username, password=p.password,
    )

    golden_records = await conn.fetch("SELECT id, query, ground_truth_chunks FROM golden")

    total_gt = 0
    total_hit_10 = 0
    total_hit_30 = 0

    for g in golden_records:
        q = g["query"]
        gt_chunks = set(g["ground_truth_chunks"])
        total_gt += len(gt_chunks)

        tsq = _build_or_tsquery(q)

        # BM25 top_10
        rows_10 = await conn.fetch(
            """SELECT id FROM chunk c WHERE c.search_vector @@ to_tsquery('simple', $1) ORDER BY ts_rank_cd(c.search_vector, to_tsquery('simple', $1)) DESC LIMIT 10""",
            tsq,
        )
        hit_10 = len(set(r["id"] for r in rows_10) & gt_chunks)
        total_hit_10 += hit_10

        # BM25 top_30
        rows_30 = await conn.fetch(
            """SELECT id FROM chunk c WHERE c.search_vector @@ to_tsquery('simple', $1) ORDER BY ts_rank_cd(c.search_vector, to_tsquery('simple', $1)) DESC LIMIT 30""",
            tsq,
        )
        hit_30 = len(set(r["id"] for r in rows_30) & gt_chunks)
        total_hit_30 += hit_30

        print(f'  query="{q[:40]}" GT={len(gt_chunks)} hit10={hit_10} hit30={hit_30}')

    recall_10 = total_hit_10 / total_gt if total_gt > 0 else 0
    recall_30 = total_hit_30 / total_gt if total_gt > 0 else 0
    print(f"\n总 GT chunks: {total_gt}")
    print(f"Recall@10: {total_hit_10}/{total_gt} = {recall_10:.2%}")
    print(f"Recall@30: {total_hit_30}/{total_gt} = {recall_30:.2%}")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(check())
