from __future__ import annotations

from argparse import ArgumentParser


def register_args(p: ArgumentParser):
    p.add_argument("--username", required=True, help="用户名")
    p.add_argument("--password", required=True, help="密码")


async def handle(args, settings):
    """创建用户"""
    from rag.infra.database.connection import init_pool, close_pool
    from rag.infra.repositories.pg_user_repository import PgUserRepository
    from rag.infra.auth.password import hash_password

    await init_pool(
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
    )

    try:
        repo = PgUserRepository()
        existing = await repo.get_by_username(args.username)
        if existing is not None:
            print(f"错误: 用户名 {args.username} 已存在")
            raise SystemExit(1)

        user = await repo.create(args.username, hash_password(args.password))
        print(f"用户 {args.username} 创建成功 (id={user.id})")
    finally:
        await close_pool()
