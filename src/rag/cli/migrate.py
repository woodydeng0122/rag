from __future__ import annotations

from argparse import ArgumentParser


def register_args(p: ArgumentParser):
    pass  # 无额外参数


async def handle(args, settings):
    """执行数据库迁移"""
    from rag.infra.database.connection import init_pool, close_pool
    from rag.infra.database.migrator import check_migrations, run_migrations

    await init_pool(
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
    )

    try:
        pending = await check_migrations()
        if not pending:
            print("数据库已是最新，无需迁移。")
            return

        print(f"待执行迁移: {', '.join(pending)}")
        await run_migrations()
        print("数据库迁移完成。")
    finally:
        await close_pool()

