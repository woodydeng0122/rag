"""BM25 全文检索快速验证脚本

用法：
    source .venv/Scripts/activate   (Windows)
    python scripts/test_bm25.py [query]
"""

import asyncio
import os
import sys
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

import asyncpg


async def main():
    # ── 读取数据库连接信息 ──
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        print("ERROR: DATABASE_URL 未设置", file=sys.stderr)
        sys.exit(1)

    parsed = urllib.parse.urlparse(database_url)
    query = sys.argv[1] if len(sys.argv) > 1 else "FastAPI"

    print(f"数据库: {parsed.hostname}:{parsed.port}/{parsed.path.lstrip('/')}")
    print(f"查询词: {query!r}")
    print("=" * 60)

    conn = await asyncpg.connect(
        host=parsed.hostname,
        port=parsed.port,
        database=parsed.path.lstrip("/"),
        user=parsed.username,
        password=parsed.password,
    )

    try:
        # ── 1. 检查 search_vector 列是否存在 ──
        col_check = await conn.fetchrow("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'chunk' AND column_name = 'search_vector'
        """)
        if not col_check:
            print("[FAIL] chunk.search_vector 列不存在！请先执行 migration 016")
            return
        print("[OK]   chunk.search_vector 列存在")

        # ── 2. 检查 search_vector 是否有数据（非 NULL） ──
        null_count_row = await conn.fetchrow("""
            SELECT COUNT(*) AS total,
                   COUNT(*) FILTER (WHERE search_vector IS NULL) AS null_cnt
            FROM chunk
        """)
        total = null_count_row["total"]
        null_cnt = null_count_row["null_cnt"]
        filled = total - null_cnt
        print(f"[INFO] chunk 总行数: {total}，search_vector 已填充: {filled}，未填充: {null_cnt}")

        if filled == 0:
            print("[FAIL] search_vector 全部为 NULL，请先回填数据")
            return

        # ── 3. 获取第一个有数据的 project ──
        project_row = await conn.fetchrow("""
            SELECT d.project_id, p.name AS project_name, COUNT(c.id) AS chunk_cnt
            FROM chunk c
            JOIN document d ON c.document_id = d.id
            JOIN project p ON d.project_id = p.id
            WHERE c.search_vector IS NOT NULL
            GROUP BY d.project_id, p.name
            ORDER BY COUNT(c.id) DESC
            LIMIT 1
        """)
        if not project_row:
            print("[FAIL] 没有可用的项目数据")
            return

        project_id = str(project_row["project_id"])
        print(f"[INFO] 测试项目: {project_row['project_name']}（{project_row['chunk_cnt']} chunks, id={project_id[:8]}...）")
        print()

        # ── 4. 执行 BM25 全文检索 ──
        print(f"执行搜索: {query!r}")
        print("-" * 60)

        rows = await conn.fetch("""
            SELECT c.id       AS chunk_id,
                   c.content,
                   ts_rank_cd(c.search_vector, plainto_tsquery('simple', $1)) AS score
            FROM chunk c
            JOIN document d ON c.document_id = d.id
            WHERE d.project_id = $2
              AND c.search_vector @@ plainto_tsquery('simple', $1)
            ORDER BY score DESC
            LIMIT 5
        """, query, project_id)

        if not rows:
            print(f"[WARN] 未找到匹配 {query!r} 的结果")
            print()
            print("提示：换一个查询词试试，例如：")
            # 从已有内容中取一个词
            sample = await conn.fetchrow("""
                SELECT content FROM chunk
                WHERE search_vector IS NOT NULL AND length(content) > 20
                LIMIT 1
            """)
            if sample:
                # 取前30个字符作为建议词
                snippet = sample["content"][:60].replace("\n", " ")
                print(f'  python scripts/test_bm25.py "{snippet}"')
            return

        print(f"[OK]   找到 {len(rows)} 条结果\n")

        for i, row in enumerate(rows, 1):
            content_preview = (row["content"] or "")[:120].replace("\n", " ")
            print(f"[{i}] score={row['score']:.6f}")
            print(f"    chunk_id: {row['chunk_id']}")
            print(f"    内容预览: {content_preview}...")
            print()

        print("=" * 60)
        print("[PASS] BM25 全文检索工作正常！")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
