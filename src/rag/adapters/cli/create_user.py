from __future__ import annotations

from argparse import ArgumentParser


def register_args(p: ArgumentParser):
    p.add_argument("--username", required=True, help="用户名")
    p.add_argument("--password", required=True, help="密码")


async def handle(args, settings):
    """创建用户，若为首个用户则自动关联现有孤立数据"""
    from rag.infra.database.connection import init_pool, close_pool, get_pool
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

        # 关联孤立数据：将 user_id 为 NULL 的 project 和 profile 关联到新用户
        pool = get_pool()
        async with pool.acquire() as conn:
            # 关联孤立项目
            result = await conn.execute(
                'UPDATE project SET user_id = $1 WHERE user_id IS NULL',
                user.id,
            )
            print(f"已关联孤立项目: {result}")

            # 迁移单例 profile（id=1, user_id IS NULL）到新用户的 profile
            old_profile = await conn.fetchrow(
                "SELECT id FROM profile WHERE id = 1 AND user_id IS NULL"
            )
            if old_profile:
                await conn.execute(
                    "UPDATE profile SET user_id = $1 WHERE id = 1 AND user_id IS NULL",
                    user.id,
                )
                print(f"已迁移单例 profile 到用户 {args.username}")
    finally:
        await close_pool()
