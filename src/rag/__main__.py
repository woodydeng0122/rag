import os
import asyncio
import argparse

os.environ["TOKENIZERS_PARALLELISM"] = "false"

def main():
    parser = argparse.ArgumentParser(description="RAG 应用")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # api 子命令
    subparsers.add_parser("api", help="启动 API 服务")

    # migrate 子命令
    subparsers.add_parser("migrate", help="执行数据库迁移")

    # ask 子命令
    p_ask = subparsers.add_parser("ask", help="提问")
    p_ask.add_argument("-q", "--query", type=str, required=True, help="查询内容")
    p_ask.add_argument("-p", "--project-id", type=str, required=True, help="项目 ID")
    p_ask.add_argument("-k", "--top-k", type=int, default=3, help="返回分块数")

    # eval 子命令
    p_eval = subparsers.add_parser("eval", help="评测")
    p_eval.add_argument("-p", "--project-id", type=str, required=True, help="项目 ID")
    p_eval.add_argument("-k", "--k", type=int, nargs="+", help="Recall@K 的 K 值")
    p_eval.add_argument("-o", "--output", type=str, default="./eval_result.json", help="结果输出文件")

    # download-embedding 子命令
    p_download = subparsers.add_parser("download-embedding", help="从 ModelScope 下载 embedding 模型")
    p_download.add_argument("-m", "--model", type=str, required=True, help="模型名称，如 iic/nlp_gte_sentence-embedding_chinese-base")
    p_download.add_argument("-o", "--output", type=str, default="./models", help="模型保存目录")

    args = parser.parse_args()
    print("[LOAD] 加载配置...", flush=True)
    from rag.bootstrap.settings import Settings
    settings = Settings.from_env()
    print("[LOAD] 配置加载完成", flush=True)

    if args.command == "migrate":
        print("[migrate] 执行数据库迁移...", flush=True)
        asyncio.run(cmd_migrate(settings))
        return

    if args.command == "download-embedding":
        print("[download] 下载 embedding 模型...", flush=True)
        from rag.cli import cmd_download_embedding
        cmd_download_embedding(args)
        return

    print("[BUILD] 构建容器...", flush=True)
    from rag.bootstrap.container import build_container
    container = build_container(settings)
    print("[BUILD] 容器构建完成", flush=True)

    if args.command == "api":
        print("[LOAD] 加载 FastAPI 应用...", flush=True)
        import uvicorn
        from rag.api.app import app
        print("[START] 启动 uvicorn 服务 (0.0.0.0:8000)...", flush=True)
        uvicorn.run(app, host="0.0.0.0", port=8000)
        return
    
    if args.command == "ask":
        from rag.cli import cmd_ask
        cmd_ask(args, ask=container.ask, project_id=args.project_id)
    elif args.command == "eval":
        from rag.cli import cmd_eval
        cmd_eval(args, evaluate=container.evaluate, project_id=args.project_id)


if __name__ == "__main__":
    main()
