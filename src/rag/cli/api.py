from __future__ import annotations

from argparse import ArgumentParser


def register_args(p: ArgumentParser):
    pass


def handle(args, container):
    import uvicorn
    from rag.api.app import app
    print("[START] 启动 uvicorn 服务 (0.0.0.0:8000)...", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=8000)
