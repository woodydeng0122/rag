"""验证新的 search_tokens 是否包含正确的英文词提取"""
import asyncio, asyncpg, os, urllib.parse
from dotenv import load_dotenv; load_dotenv()

async def c():
    url = os.getenv("DATABASE_URL","")
    p = urllib.parse.urlparse(url)
    conn = await asyncpg.connect(host=p.hostname,port=p.port,database=p.path.lstrip("/"),user=p.username,password=p.password)
    rows = await conn.fetch("SELECT id, LEFT(search_tokens,120) AS tokens FROM chunk LIMIT 5")
    print("=== 新 search_tokens 样本 ===")
    for r in rows:
        print(f"  [{r['id'][:30]}] {r['tokens']}")
    await conn.close()
asyncio.run(c())
