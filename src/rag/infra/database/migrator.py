"""轻量级数据库自动迁移 — 启动时检测并执行未运行的迁移脚本"""

import logging
from pathlib import Path

from rag.infra.database.connection import get_pool

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


async def run_migrations() -> None:
    """检查 schema_migrations 表，执行所有未运行的迁移脚本"""
    pool = get_pool()

    async with pool.acquire() as conn:
        # 1. 确保 schema_migrations 表存在
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(16) PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """)

        # 2. 获取已执行的迁移版本
        applied = await conn.fetch("SELECT version FROM schema_migrations")
        applied_versions = {row["version"] for row in applied}

    # 3. 扫描迁移目录，按文件名排序
    sql_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

    for sql_file in sql_files:
        version = sql_file.stem  # e.g. "001_init", "002_profile"

        if version in applied_versions:
            logger.info("迁移 %s 已执行，跳过", version)
            continue

        sql_content = sql_file.read_text(encoding="utf-8")
        logger.info("执行迁移 %s ...", version)

        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(sql_content)
                await conn.execute(
                    "INSERT INTO schema_migrations (version) VALUES ($1)",
                    version,
                )

        logger.info("迁移 %s 完成", version)
