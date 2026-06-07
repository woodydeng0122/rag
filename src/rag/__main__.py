import os
import asyncio
import inspect

os.environ["TOKENIZERS_PARALLELISM"] = "false"


def main():
    from rag.cli.registry import register_command, COMMANDS

    # ── 显式注册所有命令 ──────────────────────────────────
    from rag.cli.migrate import register_args as migrate_args, handle as migrate_handle
    register_command("migrate", help="执行数据库迁移", dependency="db", register_args=migrate_args, handler=migrate_handle)

    from rag.cli.download import register_args as download_args, handle as download_handle
    register_command("download-embedding", help="从 ModelScope 下载 embedding 模型", dependency="none", register_args=download_args, handler=download_handle)

    from rag.cli.list_chunks import register_args as list_chunks_args, handle as list_chunks_handle
    register_command("list-chunks", help="根据文档路径查询所有分块", dependency="db", register_args=list_chunks_args, handler=list_chunks_handle)

    from rag.cli.ask import register_args as ask_args, handle as ask_handle
    register_command("ask", help="提问", dependency="full_container", register_args=ask_args, handler=ask_handle)

    from rag.cli.evaluate import register_args as eval_args, handle as eval_handle
    register_command("eval", help="评测", dependency="full_container", register_args=eval_args, handler=eval_handle)

    from rag.cli.golden import register_args as golden_args, handle as golden_handle
    register_command("add-golden", help="将黄金数据集 item JSON 写入黄金数据集表", dependency="full_container", register_args=golden_args, handler=golden_handle)

    from rag.api.app import register_args as api_args, handle as api_handle
    register_command("api", help="启动 API 服务", dependency="full_container", register_args=api_args, handler=api_handle)

    # ── 构建 argparse ─────────────────────────────────────
    import argparse
    parser = argparse.ArgumentParser(description="RAG 应用")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for cmd in COMMANDS:
        p = subparsers.add_parser(cmd.name, help=cmd.help)
        cmd.register_args(p)

    args = parser.parse_args()

    # 查找匹配命令
    cmd = next(c for c in COMMANDS if c.name == args.command)

    # 加载配置
    print("[LOAD] 加载配置...", flush=True)
    from rag.bootstrap.settings import Settings
    settings = Settings.from_env()
    print("[LOAD] 配置加载完成", flush=True)

    # 按依赖级别分派
    if cmd.dependency == "none":
        cmd.handler(args)

    elif cmd.dependency == "db":
        result = cmd.handler(args, settings)
        if inspect.iscoroutine(result):
            asyncio.run(result)

    elif cmd.dependency == "full_container":
        print("[BUILD] 构建容器...", flush=True)
        from rag.bootstrap.container import build_container
        container = build_container(settings)
        print("[BUILD] 容器构建完成", flush=True)
        cmd.handler(args, container)


if __name__ == "__main__":
    main()
