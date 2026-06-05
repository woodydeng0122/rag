
from rag.application.usecases.ask import AskUseCase
from rag.application.usecases.evaluate import EvaluateUseCase


def cmd_ask(args, ask: AskUseCase, project_id: str):
    """提问命令"""
    query = args.query
    if not query:
        raise ValueError("请提供查询内容: -q/--query")

    print(f"======================= 提问 =======================")
    print(query)

    import asyncio
    result = asyncio.run(ask.execute(query=query, project_id=project_id, top_k=args.top_k))

    print(f"======================= 回答 =======================")
    print(result.answer)


def cmd_eval(args, evaluate: EvaluateUseCase, project_id: str):
    """评测命令"""
    import asyncio

    # 从 DB 获取项目的黄金记录 ID
    from rag.bootstrap.container import get_container
    container = get_container()
    records = asyncio.run(container.golden_dataset_usecase.list_by_project(project_id))
    golden_ids = [r.id for r in records if r.ground_truth_chunks]

    if not golden_ids:
        print("该项目没有黄金记录，无法评测。")
        return

    k_list = args.k or [10]
    result = asyncio.run(evaluate.execute_by_project(
        project_id=project_id,
        golden_ids=golden_ids,
        k_list=k_list,
    ))

    import json
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump({
            "time": result.time,
            "answerable_count": result.answerable_count,
            "recall": result.recall,
            "mrr": result.mrr,
            "latency_total_ms": result.latency_total_ms,
            "latency_avg_ms": result.latency_avg_ms,
            "failure": result.failure,
        }, f, ensure_ascii=False, indent=2)
    print(f"评测结果已保存到 {args.output}")


async def cmd_migrate():
    """执行数据库迁移"""
    from rag.bootstrap.settings import Settings
    from rag.infra.database.connection import init_pool, close_pool
    from rag.infra.database.migrator import check_migrations, run_migrations

    settings = Settings.from_env()
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
