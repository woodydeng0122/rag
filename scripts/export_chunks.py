"""导出所有 chunk ID 及其 heading/content 摘要，用于匹配 golden_testset"""
import asyncio
import json
import os
import urllib.parse
from dotenv import load_dotenv
load_dotenv()

import asyncpg


async def main():
    database_url = os.getenv("DATABASE_URL", "")
    if database_url:
        parsed = urllib.parse.urlparse(database_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 5432
        db_name = parsed.path.lstrip("/") or "rag-db"
        user = parsed.username or "admin"
        password = parsed.password or "password"
    else:
        host = os.getenv("DB_HOST", "localhost")
        port = int(os.getenv("DB_PORT", "5434"))
        db_name = os.getenv("DB_NAME", "rag-db")
        user = os.getenv("DB_USER", "admin")
        password = os.getenv("DB_PASSWORD", "password")

    conn = await asyncpg.connect(
        host=host, port=port, database=db_name,
        user=user, password=password, ssl=False,
    )

    rows = await conn.fetch("""
        SELECT c.id, c.heading, LEFT(c.content, 120) AS content_preview, c.source_file,
               d.filename, d.project_id
        FROM chunk c
        JOIN document d ON c.document_id = d.id
        ORDER BY d.filename, c.index
    """)

    result = []
    for r in rows:
        result.append({
            "chunk_id": r["id"],
            "heading": r["heading"],
            "content_preview": r["content_preview"],
            "source_file": r["source_file"],
            "filename": r["filename"],
            "project_id": str(r["project_id"]),
        })

    await conn.close()

    output_path = os.path.join(os.path.dirname(__file__), "chunks_export.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Exported {len(result)} chunks to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
