"""应用启动初始化 — 连接池 + 自动迁移"""

import logging

from rag.infra.database.connection import init_pool
from rag.infra.database.migrator import run_migrations
from rag.bootstrap.settings import Settings

logger = logging.getLogger(__name__)


async def startup() -> None:
    """应用启动时调用：初始化数据库连接池，执行未运行的迁移"""
    settings = Settings.from_env()

    # 1. 初始化连接池
    await init_pool(
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
    )
    logger.info("数据库连接池已初始化")

    # 2. 自动迁移
    await run_migrations()
    logger.info("数据库迁移检查完成")
