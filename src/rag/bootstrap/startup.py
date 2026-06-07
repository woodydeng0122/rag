"""应用启动/关闭初始化 — 连接池 + 迁移校验 + 模型扫描"""
from rag.infra.database.connection import init_pool, close_pool
from rag.infra.database.migrator import check_migrations

async def startup(container) -> None:
    settings = container.settings
    # 1. 初始化连接池
    print("[INIT] 初始化数据库连接池...", flush=True)
    await init_pool(
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
    )
    print("[INIT] 数据库连接池已初始化", flush=True)

    # 2. 校验迁移状态（不执行迁移，仅检查）
    print("[CHECK] 校验数据库迁移状态...", flush=True)
    pending = await check_migrations()
    if pending:
        raise RuntimeError(
            f"数据库迁移未完成！待执行: {', '.join(pending)}。请运行: python -m rag migrate"
        )
    print("[CHECK] 数据库迁移校验通过", flush=True)

    # 3. 扫描本地嵌入模型（通过 get_container 复用单例，避免重复构建）
    print("[SCAN] 扫描本地嵌入模型...", flush=True)
    models = await container.scan_embed_models_usecase.execute()
    online_count = sum(1 for m in models if m.is_online)
    print(f"[SCAN] 嵌入模型扫描完成: {len(models)} 个模型, {online_count} 个 online", flush=True)


async def shutdown() -> None:
    """应用关闭时调用：关闭数据库连接池"""
    await close_pool()
    print("[CLOSE] 数据库连接池已关闭", flush=True)
