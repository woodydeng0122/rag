from __future__ import annotations

from argparse import ArgumentParser


def register_args(p: ArgumentParser):
    p.add_argument("-q", "--query", type=str, required=True, help="查询内容")
    p.add_argument("-p", "--project-id", type=str, required=True, help="项目 ID")
    p.add_argument("-k", "--top-k", type=int, default=3, help="返回分块数")


def handle(args, container):
    """提问命令"""
    query = args.query
    if not query:
        raise ValueError("请提供查询内容: -q/--query")

    print(f"======================= 提问 =======================")
    print(query)

    import asyncio
    result = asyncio.run(container.ask.execute(query=query, project_id=args.project_id, top_k=args.top_k))

    print(f"======================= 回答 =======================")
    print(result.answer)

