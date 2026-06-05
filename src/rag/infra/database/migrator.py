"""轻量级数据库迁移 — 启动时校验 + CLI 手动执行"""

import logging
from pathlib import Path

from rag.infra.database.connection import get_pool

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def _scan_migration_files() -> list[Path]:
    """扫描迁移目录，按文件名排序返回 SQL 文件列表"""
    return sorted(MIGRATIONS_DIR.glob("*.sql"))


async def _get_applied_versions() -> set[str]:
    """获取已执行的迁移版本集合"""
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(64) PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """)
        applied = await conn.fetch("SELECT version FROM schema_migrations")
        return {row["version"] for row in applied}


async def check_migrations() -> list[str]:
    """校验所有迁移是否已执行，返回未执行的版本列表。
    如果返回空列表，说明数据库已是最新。"""
    applied = await _get_applied_versions()
    pending = []
    for sql_file in _scan_migration_files():
        version = sql_file.stem
        if version not in applied:
            pending.append(version)
    return pending


async def run_migrations() -> None:
    """执行所有未运行的迁移脚本"""
    pool = get_pool()
    applied = await _get_applied_versions()

    for sql_file in _scan_migration_files():
        version = sql_file.stem

        if version in applied:
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
