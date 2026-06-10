import os
import asyncio
import inspect

os.environ["TOKENIZERS_PARALLELISM"] = "false"


def main():
    from rag.adapters.cli.registry import register_command, COMMANDS

    # ── 延迟注册所有命令 — 仅在执行时才 import 模块 ──────────
    register_command("migrate", help="执行数据库迁移", dependency="db", lazy_import="rag.adapters.cli.migrate")
    register_command("create-user", help="创建用户", dependency="db", lazy_import="rag.adapters.cli.create_user")
    register_command("download-embedding", help="从 ModelScope 下载 embedding 模型", dependency="none", lazy_import="rag.adapters.cli.download")
    register_command("list-chunks", help="根据文档路径查询所有分块", dependency="db", lazy_import="rag.adapters.cli.list_chunks")
    register_command("list-projects", help="列出所有项目", dependency="db", lazy_import="rag.adapters.cli.list_projects")
    register_command("ask", help="提问", dependency="full_container", lazy_import="rag.adapters.cli.ask")
    register_command("api", help="启动 API 服务", dependency="full_container", lazy_import="rag.adapters.cli.api")
    register_command("miss", help="筛选项目中检索未命中的黄金记录", dependency="db", lazy_import="rag.adapters.cli.miss")

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
