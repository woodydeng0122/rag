import asyncpg

_pool: asyncpg.Pool | None = None


async def init_pool(
    host: str = "localhost",
    port: int = 5434,
    database: str = "rag-db",
    user: str = "admin",
    password: str = "password",
    min_size: int = 2,
    max_size: int = 10,
) -> asyncpg.Pool:
    """创建 asyncpg 连接池"""
    global _pool
    _pool = await asyncpg.create_pool(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
        min_size=min_size,
        max_size=max_size,
        ssl=False,
    )
    return _pool


def get_pool() -> asyncpg.Pool:
    """获取当前连接池，未初始化时抛出异常"""
    if _pool is None:
        raise RuntimeError("数据库连接池未初始化，请先调用 init_pool()")
    return _pool


async def close_pool() -> None:
    """关闭连接池"""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


class db_connection:
    """CLI 脚本数据库连接上下文管理器，自动初始化和关闭连接池"""

    def __init__(self, settings):
        self._settings = settings

    async def __aenter__(self) -> asyncpg.Pool:
        return await init_pool(
            host=self._settings.db_host,
            port=self._settings.db_port,
            database=self._settings.db_name,
            user=self._settings.db_user,
            password=self._settings.db_password,
        )

    async def __aexit__(self, *exc):
        await close_pool()
