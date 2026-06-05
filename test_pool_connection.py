import asyncio
import asyncpg

async def test():
    try:
        pool = await asyncpg.create_pool(
            host='192.168.10.26',
            port=5434,
            database='rag-db',
            user='admin',
            password='password',
            ssl=False,
            min_size=1,
            max_size=2
        )
        async with pool.acquire() as conn:
            result = await conn.fetchval('SELECT 1')
            print(f'连接池测试成功! 结果: {result}')
        await pool.close()
    except Exception as e:
        print(f'连接失败: {type(e).__name__}: {e}')

asyncio.run(test())
