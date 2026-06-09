from argparse import ArgumentParser


def register_args(p: ArgumentParser):
    pass


def handle(args, container):
    from rag.adapters.api.app import app
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
