from __future__ import annotations


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
