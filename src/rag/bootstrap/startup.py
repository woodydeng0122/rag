"""应用启动初始化 — 连接池 + 迁移校验 + 模型扫描"""

import logging

from rag.infra.database.connection import init_pool
from rag.infra.database.migrator import check_migrations
from rag.bootstrap.settings import Settings
from rag.bootstrap.container import build_container

logger = logging.getLogger(__name__)


async def startup() -> None:
    """应用启动时调用：初始化数据库连接池，校验迁移状态，扫描嵌入模型"""
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

    # 2. 校验迁移状态（不执行迁移，仅检查）
    pending = await check_migrations()
    if pending:
        raise RuntimeError(
            f"数据库迁移未完成！待执行: {', '.join(pending)}。请运行: python -m rag migrate"
        )
    logger.info("数据库迁移校验通过")

    # 3. 扫描本地嵌入模型
    container = build_container(settings)
    models = await container.scan_embed_models_usecase.execute()
    online_count = sum(1 for m in models if m.is_online)
    logger.info(f"嵌入模型扫描完成: {len(models)} 个模型, {online_count} 个 online")
