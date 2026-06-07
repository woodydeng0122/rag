from __future__ import annotations

from argparse import ArgumentParser


def register_args(p: ArgumentParser):
    p.add_argument("-p", "--path", type=str, required=True, help="文档路径（storage_key），如 docs/4d73bb12-fea0-4d0d-8e51-8161c3804a71/docs/alternatives.md")


async def handle(args, settings):
    """根据文档路径查询所有分块"""
    from rag.infra.database.connection import init_pool, close_pool
    from rag.infra.repositories.pg_document_repository import PgDocumentRepository
    from rag.infra.repositories.pg_chunk_repository import PgChunkRepository

    storage_key = args.path

    await init_pool(
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
    )
    try:
        doc_repo = PgDocumentRepository()
        chunk_repo = PgChunkRepository()

        doc = await doc_repo.get_by_storage_key(storage_key)
        if doc is None:
            print(f"未找到文档: {storage_key}")
            return
        print(f"项目 ID: {doc.project_id}")
        print(f"文档 ID: {doc.id}")
        print(f"文件名: {doc.filename}")
        print(f"状态: {doc.status}")
        print(f"分块数: {doc.chunk_count}")
        print("=" * 60)

        chunks = await chunk_repo.list_by_document(doc.id)
        if not chunks:
            print("无分块数据")
            return

        for c in chunks:
            print(f"\n--- 分块 [{c.index}] id={c.id} ---")
            if c.heading:
                print(f"标题: {c.heading}")
            if c.source_file:
                print(f"源文件: {c.source_file}")
            print(c.content)
    finally:
        await close_pool()

