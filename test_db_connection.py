import asyncio
import asyncpg

async def test():
    try:
        conn = await asyncpg.connect(
            host='192.168.10.26',
            port=5434,
            database='rag-db',
            user='admin',
            password='password'
        )
        print('连接成功!')
        await conn.close()
    except Exception as e:
        print(f'连接失败: {type(e).__name__}: {e}')

asyncio.run(test())
