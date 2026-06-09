from contextlib import asynccontextmanager

from rag.infra.database.connection import get_pool


def to_uuid(value: str) -> str:
    """确保值是合法的 UUID 字符串，asyncpg 会自动转换"""
    return value


@asynccontextmanager
async def acquire_connection():
    """获取数据库连接的上下文管理器，消除每个方法重复的 pool.acquire 样板代码"""
    pool = get_pool()
    async with pool.acquire() as conn:
        yield conn


class BaseRepository:
    """Repository 基类，提供公共的数据库操作方法"""

    async def _delete_by_id(self, table: str, id_value: str, id_column: str = "id") -> bool:
        async with acquire_connection() as conn:
            result = await conn.execute(
                f"DELETE FROM {table} WHERE {id_column} = $1",
                to_uuid(id_value) if id_column == "id" else id_value,
            )
        return result == "DELETE 1"

    async def _fetch_one(self, sql: str, *args):
        async with acquire_connection() as conn:
            return await conn.fetchrow(sql, *args)

    async def _fetch_all(self, sql: str, *args):
        async with acquire_connection() as conn:
            return await conn.fetch(sql, *args)

    async def _execute(self, sql: str, *args):
        async with acquire_connection() as conn:
            return await conn.execute(sql, *args)
