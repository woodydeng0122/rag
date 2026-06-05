import os
import argparse

os.environ["TOKENIZERS_PARALLELISM"] = "false"
from rag.bootstrap import Settings, build_container, Container
from rag.cli.commands import cmd_ask, cmd_eval


def start_api(container: Container):
    """启动 API 服务"""
    import uvicorn
    from rag.api.app import app
    app.state.container = container
    uvicorn.run(app, host="0.0.0.0", port=8000)


def main():
    parser = argparse.ArgumentParser(description="RAG 应用")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # api 子命令
    subparsers.add_parser("api", help="启动 API 服务")

    # ask 子命令
    p_ask = subparsers.add_parser("ask", help="提问")
    p_ask.add_argument("-q", "--query", type=str, help="查询内容")
    p_ask.add_argument("-i", "--index", type=int, default=0, help="黄金集第几条")
    p_ask.add_argument("-k", "--top-k", type=int, default=3, help="返回分块数")

    # eval 子命令
    p_eval = subparsers.add_parser("eval", help="评测")
    p_eval.add_argument("-k", "--k", type=int, nargs="+", help="Recall@K 的 K 值")
    p_eval.add_argument("-o", "--output", type=str, default="./eval_result.json", help="结果输出文件")

    args = parser.parse_args()
    settings = Settings()
    container = build_container(settings)

    if args.command == "api":
        start_api(container)
    elif args.command == "ask":
        cmd_ask(args, ask=container.ask, golden_file=container.settings.golden_file)
    elif args.command == "eval":
        cmd_eval(args, evaluate=container.evaluate, golden_file=container.settings.golden_file)


if __name__ == "__main__":
    main()
